#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LZ-PDF 合并 - PyQt5 无边框美化窗口

功能目标：
- 选择多个 PDF 文件，支持上移/下移、移除与清空列表
- 选择输出文件夹与文件名
- 线程化执行合并，显示进度与状态
- 与项目现有 ui_style_nb 保持一致的样式与行为

依赖：PyQt5、PyMuPDF
"""

import os
import sys
from typing import Callable, List, Optional

import fitz  # PyMuPDF

from PySide6.QtCore import Qt, QThread, Signal, QPoint, QSize, QUrl, QCoreApplication, QTimer
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QLineEdit,
    QFrame,
    QStyle,
    QFormLayout,
    QSizePolicy,
    QCheckBox,
    QAbstractItemView,
    QInputDialog,
)
from PySide6.QtGui import QDesktopServices

from ui_style_nb import build_style, compute_scale, dp


# 可配置：联系网址（与其他页面保持一致用法）
CONTACT_URL = "https://www.example.com/"


# ----------------- 功能函数（可被其他项目直接调用） -----------------
def merge_pdfs(
    input_paths: List[str],
    output_path: str,
    progress_cb: Optional[Callable[[int, str], None]] = None,
    keep_toc: bool = True,
    keep_metadata: bool = True,
) -> str:
    """将多个 PDF 合并为一个 PDF。

    Args:
        input_paths: 输入 PDF 路径列表（按顺序合并）。
        output_path: 输出 PDF 文件路径。
        progress_cb: 进度回调 (pct: 0-100, msg: str)。

    Returns:
        生成的输出 PDF 路径（成功时）。
    """

    if not input_paths:
        raise ValueError("请至少选择一个 PDF 文件")

    out_dir = os.path.dirname(output_path) or os.getcwd()
    os.makedirs(out_dir, exist_ok=True)

    # 以“文件数”为粒度进行进度上报，避免预先统计页数的成本
    total_files = len(input_paths)
    new_doc = fitz.open()
    combined_toc = []
    first_metadata = None
    try:
        for idx, p in enumerate(input_paths, 1):
            if not os.path.exists(p):
                raise FileNotFoundError(f"文件不存在: {p}")
            if progress_cb:
                try:
                    progress_cb(int((idx - 1) * 100 / total_files), f"打开: {os.path.basename(p)}")
                except Exception:
                    pass
            # 记录当前目标文档页偏移
            try:
                offset = new_doc.page_count
            except Exception:
                offset = 0
            src = fitz.open(p)
            try:
                if first_metadata is None:
                    try:
                        first_metadata = src.metadata
                    except Exception:
                        first_metadata = None
                if keep_toc:
                    try:
                        toc = src.get_toc() or []
                        for it in toc:
                            if len(it) >= 3:
                                lvl, title, page = it[0], it[1], it[2]
                                combined_toc.append([lvl, title, page + offset])
                    except Exception:
                        pass
                new_doc.insert_pdf(src)
            finally:
                try:
                    src.close()
                except Exception:
                    pass
            if progress_cb:
                try:
                    progress_cb(int(idx * 100 / total_files), f"已合并: {os.path.basename(p)}")
                except Exception:
                    pass

        # 应用目录（书签）
        if keep_toc and combined_toc:
            try:
                new_doc.set_toc(combined_toc)
            except Exception:
                pass
        # 应用元数据（保留首个文件）
        if keep_metadata and first_metadata:
            try:
                new_doc.set_metadata(dict(first_metadata))
            except Exception:
                pass

        new_doc.save(output_path)
        if progress_cb:
            try:
                progress_cb(100, f"完成，保存至: {output_path}")
            except Exception:
                pass
        return output_path
    finally:
        try:
            new_doc.close()
        except Exception:
            pass


# ----------------- 工作线程 -----------------
class MergeWorker(QThread):
    progress = Signal(int, str)
    success = Signal(str)
    failed = Signal(str)

    def __init__(self, input_paths: List[str], output_path: str, keep_toc: bool = True, keep_metadata: bool = True):
        super().__init__()
        self.input_paths = input_paths
        self.output_path = output_path
        self.keep_toc = keep_toc
        self.keep_metadata = keep_metadata

    def run(self):
        def cb(pct: int, msg: str):
            try:
                self.progress.emit(int(pct), str(msg))
            except Exception:
                pass

        try:
            result = merge_pdfs(
                self.input_paths,
                self.output_path,
                cb,
                keep_toc=self.keep_toc,
                keep_metadata=self.keep_metadata,
            )
            if result and os.path.exists(result):
                self.success.emit(result)
            else:
                self.failed.emit("合并失败：未生成输出文件")
        except Exception as e:
            self.failed.emit(str(e))


# ----------------- 界面代码（PyQt5） -----------------
class PDFMergeWindow(QWidget):
    def __init__(self, scale: Optional[float] = None, embedded: bool = False):
        super().__init__()
        # 根据 embedded 决定窗口标志，避免后续切换导致内部对象（布局）被销毁
        try:
            self.setWindowFlags(Qt.Widget if embedded else (Qt.FramelessWindowHint | Qt.Window))
        except Exception:
            pass
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())
        self.embedded = embedded
        self.resize(dp(self.scale, 900), dp(self.scale, 600))
        self._drag_pos: Optional[QPoint] = None

        # 状态
        self.output_dir: Optional[str] = None
        self.output_name: str = "merged.pdf"
        self.worker: Optional[MergeWorker] = None

        self.setStyleSheet(build_style(self.scale))
        # 支持窗口级别外部拖放添加文件
        self.setAcceptDrops(True)
        self._build_ui()

    # ---- Frameless 拖动支持 ----
    def mousePressEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and hasattr(self, "title_bar")
            and self.title_bar.isVisible()
            and self.title_bar.rect().contains(event.pos())
        ):
            top = self if self.isWindow() else self.window()
            self._drag_pos = event.globalPos() - top.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            top = self if self.isWindow() else self.window()
            top.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
        root.setSpacing(dp(self.scale, 8))

        # 顶部标题栏
        self.title_bar = QFrame(self)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
        title_layout.setSpacing(dp(self.scale, 6))
        title = QLabel("LZ-PDF 合并")
        title.setObjectName("Title")
        title_layout.addWidget(title)
        title_layout.addStretch(1)
        btn_size = QPushButton("窗口大小")
        btn_size.clicked.connect(self._on_set_size)
        btn_full = QPushButton("全屏")
        btn_full.clicked.connect(self._on_toggle_fullscreen)
        style = self.style()
        btn_full.setIcon(style.standardIcon(QStyle.SP_TitleBarMaxButton))
        btn_full.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_size.setIcon(style.standardIcon(QStyle.SP_DesktopIcon))
        btn_size.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_min = QPushButton("")
        btn_min.setIcon(style.standardIcon(QStyle.SP_TitleBarMinButton))
        btn_min.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_min.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
        btn_min.clicked.connect(lambda: (self if self.isWindow() else self.window()).showMinimized())
        btn_close = QPushButton("")
        btn_close.setIcon(style.standardIcon(QStyle.SP_TitleBarCloseButton))
        btn_close.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_close.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
        btn_close.clicked.connect(lambda: (self if self.isWindow() else self.window()).close())
        title_layout.addWidget(btn_size)
        title_layout.addWidget(btn_full)
        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_close)
        root.addWidget(self.title_bar)

        if self.embedded:
            self.title_bar.hide()
        if not self.isWindow():
            btn_min.hide()
            btn_close.hide()

        # 主体：左文件列表 + 右参数与操作
        self.main_row = QHBoxLayout()
        self.main_row.setSpacing(dp(self.scale, 8))

        # 左：文件列表卡片
        self.left_card = QFrame(self)
        self.left_card.setObjectName("PanelCard")
        left = QVBoxLayout(self.left_card)
        left.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))
        left.setSpacing(dp(self.scale, 8))

        btn_add_files = QPushButton("添加文件")
        btn_add_files.setMinimumHeight(dp(self.scale, 48))
        btn_add_files.clicked.connect(self._on_add_files)
        btn_add_folder = QPushButton("添加文件夹")
        btn_add_folder.setMinimumHeight(dp(self.scale, 48))
        btn_add_folder.clicked.connect(self._on_add_folder)
        left.addWidget(btn_add_files)
        left.addWidget(btn_add_folder)

        self.files_list = QListWidget(self)
        self.files_list.setMinimumHeight(dp(self.scale, 240))
        # 启用内部拖拽排序与外部拖放
        self.files_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.files_list.setDragEnabled(True)
        self.files_list.setAcceptDrops(True)
        self.files_list.setDropIndicatorShown(True)
        self.files_list.setDragDropMode(QAbstractItemView.InternalMove)
        left.addWidget(self.files_list, 1)

        ops_row = QHBoxLayout()
        ops_row.setSpacing(dp(self.scale, 6))
        btn_up = QPushButton("上移")
        btn_up.clicked.connect(self._on_move_up)
        btn_down = QPushButton("下移")
        btn_down.clicked.connect(self._on_move_down)
        btn_remove = QPushButton("移除选中")
        btn_remove.clicked.connect(self._on_remove_selected)
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self._on_clear)
        btn_bulk = QPushButton("批量清理")
        btn_bulk.clicked.connect(self._on_bulk_clean)
        ops_row.addWidget(btn_up)
        ops_row.addWidget(btn_down)
        ops_row.addWidget(btn_remove)
        ops_row.addWidget(btn_clear)
        ops_row.addWidget(btn_bulk)
        left.addLayout(ops_row)

        self.main_row.addWidget(self.left_card, 3)

        # 右：参数与操作卡片
        self.right_card = QFrame(self)
        self.right_card.setObjectName("PanelCard")
        right = QVBoxLayout(self.right_card)
        right.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))
        right.setSpacing(dp(self.scale, 8))

        # 输出路径设置
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setPlaceholderText("输出文件夹（默认：首个文件同目录）")
        self.output_dir_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_pick_out = QPushButton("选择输出路径")
        btn_pick_out.clicked.connect(self._on_pick_output_dir)

        self.output_name_edit = QLineEdit(self.output_name)
        self.output_name_edit.setPlaceholderText("输出文件名，例如 merged.pdf")
        self.output_name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        path_form = QFormLayout()
        path_form.setLabelAlignment(Qt.AlignRight)
        path_form.setFormAlignment(Qt.AlignLeft)
        path_form.setHorizontalSpacing(dp(self.scale, 8))
        path_form.setVerticalSpacing(dp(self.scale, 6))
        # 字段随空间增长，必要时换行以避免溢出
        path_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        path_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        label_w = dp(self.scale, 90)
        lbl_out_dir = QLabel("输出路径"); lbl_out_dir.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lbl_out_dir.setFixedWidth(label_w)
        lbl_out_name = QLabel("输出文件"); lbl_out_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lbl_out_name.setFixedWidth(label_w)
        right.addWidget(btn_pick_out)
        path_form.addRow(lbl_out_dir, self.output_dir_edit)
        path_form.addRow(lbl_out_name, self.output_name_edit)
        right.addLayout(path_form)

        # 合并参数
        param_form = QFormLayout()
        param_form.setLabelAlignment(Qt.AlignRight)
        param_form.setFormAlignment(Qt.AlignLeft)
        param_form.setHorizontalSpacing(dp(self.scale, 8))
        param_form.setVerticalSpacing(dp(self.scale, 4))
        param_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        param_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.keep_toc_cb = QCheckBox("保留书签/目录")
        self.keep_toc_cb.setChecked(True)
        self.keep_meta_cb = QCheckBox("保留元数据（Title/Author 等）")
        self.keep_meta_cb.setChecked(True)
        lbl_params = QLabel("合并参数")
        lbl_params.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        param_box = QVBoxLayout()
        param_box.setSpacing(dp(self.scale, 2))
        param_box.addWidget(self.keep_toc_cb)
        param_box.addWidget(self.keep_meta_cb)
        holder = QFrame(self)
        holder.setLayout(param_box)
        param_form.addRow(lbl_params, holder)
        right.addLayout(param_form)

        # 操作区
        self.act_row = QHBoxLayout()
        self.act_row.setSpacing(dp(self.scale, 6))
        self.btn_merge = QPushButton("开始合并")
        self.btn_merge.setMinimumHeight(dp(self.scale, 36))
        self.btn_merge.clicked.connect(self._on_start_merge)

        self.btn_open = QPushButton("打开输出")
        self.btn_open.setMinimumHeight(dp(self.scale, 36))
        self.btn_open.clicked.connect(self._on_open_output)

        btn_contact = QPushButton("联系我们")
        btn_contact.setMinimumHeight(dp(self.scale, 36))
        btn_contact.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(CONTACT_URL)))

        self.act_row.addWidget(self.btn_merge)
        self.act_row.addWidget(self.btn_open)
        self.act_row.addWidget(btn_contact)
        right.addLayout(self.act_row)

        # 进度与状态
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setMinimumHeight(dp(self.scale, 16))
        right.addWidget(self.progress)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        right.addWidget(self.status_label)

        self.main_row.addWidget(self.right_card, 2)
        root.addLayout(self.main_row)
        # 初始进行一次响应式布局调整
        QTimer.singleShot(0, self._reflow_layout)
        # 初始进行一次自适应高度，避免字体裁剪
        QTimer.singleShot(0, self._apply_responsive_sizes)
        # 每秒自动检测并重排
        self._auto_timer = QTimer(self)
        self._auto_timer.setInterval(1000)
        self._auto_timer.timeout.connect(self._reflow_layout)
        self._auto_timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self._reflow_layout()
            self._apply_responsive_sizes()
        except Exception:
            pass

    def _reflow_layout(self):
        # 根据当前可用宽度，决定左右并排或上下堆叠
        # 防御：main_row 在某些窗口标志切换或销毁场景下可能失效
        try:
            import shiboken6
        except Exception:
            shiboken6 = None
        if not hasattr(self, "main_row"):
            return
        if shiboken6 and hasattr(shiboken6, "isValid") and not shiboken6.isValid(self.main_row):
            return
        try:
            spacing = self.main_row.spacing()
        except RuntimeError:
            return
        m = self.contentsMargins()
        avail_w = max(0, self.width() - m.left() - m.right())
        left_w = self.left_card.sizeHint().width()
        right_w = self.right_card.sizeHint().width()
        need_w = left_w + right_w + spacing
        self.main_row.setDirection(QBoxLayout.LeftToRight if need_w <= avail_w else QBoxLayout.TopToBottom)
        # 窄屏下操作按钮垂直排列，避免拥挤；宽屏下保持水平
        self.act_row.setDirection(QBoxLayout.LeftToRight if self.width() >= dp(self.scale, 900) else QBoxLayout.TopToBottom)

    def _calc_size_factor(self) -> float:
        """依据右侧卡片可用空间计算高度因子，空间不足时压缩控件高度。"""
        try:
            base_w = max(1, dp(self.scale, 420))
            panel_w = max(1, self.right_card.width())
            factor_w = panel_w / float(base_w)

            lay = self.right_card.layout()
            need_h = 0
            if lay is not None:
                for i in range(lay.count()):
                    it = lay.itemAt(i)
                    w = it.widget(); l = it.layout(); s = it.spacerItem()
                    if w is not None:
                        need_h += w.minimumSizeHint().height()
                    elif l is not None:
                        need_h += l.minimumSize().height()
                    elif s is not None:
                        need_h += s.sizeHint().height()
                need_h += max(0, lay.count() - 1) * lay.spacing()
                m = lay.contentsMargins(); need_h += m.top() + m.bottom()
            else:
                need_h = dp(self.scale, 640)

            avail_h = max(1, self.right_card.height())
            ratio_h = min(1.0, avail_h / float(max(1, need_h)))
            f = (factor_w * 0.6 + ratio_h * 0.4)
            return max(0.55, min(1.15, f))
        except Exception:
            return 1.0

    def _apply_responsive_sizes(self):
        """设置控件最小高度，并以字体度量作下限避免文字裁剪。"""
        try:
            f = self._calc_size_factor()
            def H(base: int) -> int:
                return int(dp(self.scale, base) * f)
            def ensure_h(w, base: int, extra: int = 10):
                try:
                    fm_h = w.fontMetrics().height() + dp(self.scale, extra)
                except Exception:
                    fm_h = dp(self.scale, base)
                w.setMinimumHeight(max(H(base), fm_h))

            # 左侧操作按钮与列表
            # 注意：这些按钮在 _build_ui 中局部变量创建，无法直接引用；仅统一列表高度
            self.files_list.setMinimumHeight(H(200))

            # 右侧路径表单与操作按钮
            ensure_h(self.output_dir_edit, 32)
            ensure_h(self.output_name_edit, 32)
            ensure_h(self.btn_merge, 36)
            ensure_h(self.btn_open, 36)

            # 进度与状态
            ensure_h(self.progress, 22, extra=6)
            ensure_h(self.status_label, 24, extra=4)
        except Exception:
            pass

    # ---- 标题栏操作 ----
    def _on_toggle_fullscreen(self):
        top = self if self.isWindow() else self.window()
        if top.isFullScreen():
            top.showNormal()
        else:
            top.showFullScreen()

    def _on_set_size(self):
        top = self if self.isWindow() else self.window()
        w, ok1 = QInputDialog.getInt(self, "设置宽度", "宽度(px):", top.width(), 800, 3840, 10)
        if not ok1:
            return
        h, ok2 = QInputDialog.getInt(self, "设置高度", "高度(px):", top.height(), 600, 2160, 10)
        if not ok2:
            return
        top.resize(w, h)

    # ---- 文件列表操作 ----
    def _on_add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择PDF文件", os.getcwd(), "PDF 文件 (*.pdf)")
        if paths:
            self._add_paths(paths)

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含PDF的文件夹", os.getcwd())
        if not folder:
            return
        pdfs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        if not pdfs:
            QMessageBox.information(self, "提示", "该文件夹未找到 PDF 文件")
            return
        self._add_paths(pdfs)

    def _add_paths(self, paths: List[str]):
        # 去重：避免重复添加；保持现有顺序 + 新增顺序
        existing = set(self._collect_paths())
        added = 0
        for p in paths:
            if p not in existing:
                self.files_list.addItem(QListWidgetItem(p))
                existing.add(p)
                added += 1
        if added:
            # 设定默认输出路径（首个文件同目录）
            self._suggest_output()
            self.status_label.setText(f"已添加 {added} 个文件")

    def _on_bulk_clean(self):
        # 批量清理：移除临时/无效/重复项
        paths = self._collect_paths()
        cleaned = []
        seen = set()
        removed = 0
        for p in paths:
            name = os.path.basename(p)
            if not p.lower().endswith('.pdf'):
                removed += 1
                continue
            if name.startswith('~$'):
                removed += 1
                continue
            if not os.path.exists(p):
                removed += 1
                continue
            if p in seen:
                removed += 1
                continue
            seen.add(p)
            cleaned.append(p)
        self.files_list.clear()
        for p in cleaned:
            self.files_list.addItem(QListWidgetItem(p))
        if cleaned:
            self._suggest_output()
        self.status_label.setText(f"已清理 {removed} 项；保留 {len(cleaned)} 项")

    def _on_move_up(self):
        row = self.files_list.currentRow()
        if row > 0:
            item = self.files_list.takeItem(row)
            self.files_list.insertItem(row - 1, item)
            self.files_list.setCurrentRow(row - 1)

    def _on_move_down(self):
        row = self.files_list.currentRow()
        if 0 <= row < self.files_list.count() - 1:
            item = self.files_list.takeItem(row)
            self.files_list.insertItem(row + 1, item)
            self.files_list.setCurrentRow(row + 1)

    def _on_remove_selected(self):
        row = self.files_list.currentRow()
        if row >= 0:
            self.files_list.takeItem(row)

    def _on_clear(self):
        self.files_list.clear()
        self.status_label.setText("列表已清空")

    def _collect_paths(self) -> List[str]:
        return [self.files_list.item(i).text() for i in range(self.files_list.count())]

    # ---- 输出路径 ----
    def _suggest_output(self):
        paths = self._collect_paths()
        if not paths:
            return
        first = paths[0]
        out_dir = os.path.dirname(first)
        self.output_dir = out_dir
        self.output_dir_edit.setText(out_dir)
        # 保持当前 output_name_edit 文本，若为空则默认 merged.pdf
        name = (self.output_name_edit.text().strip() or "merged.pdf")
        self.output_name_edit.setText(name)

    def _on_pick_output_dir(self):
        dir_ = QFileDialog.getExistingDirectory(self, "选择输出文件夹", self.output_dir or os.getcwd())
        if dir_:
            self.output_dir = dir_
            self.output_dir_edit.setText(dir_)

    def _build_output_path(self) -> str:
        name = self.output_name_edit.text().strip() or "merged.pdf"
        if not name.lower().endswith('.pdf'):
            name += '.pdf'
        out_dir = self.output_dir or os.getcwd()
        return os.path.join(out_dir, name)

    # ---- 合并执行 ----
    def _on_start_merge(self):
        paths = self._collect_paths()
        if not paths:
            QMessageBox.information(self, "提示", "请先添加需要合并的 PDF 文件")
            return
        output_path = self._build_output_path()
        self.progress.setValue(0)
        self.status_label.setText("正在合并...")
        self._set_controls_enabled(False)

        self.worker = MergeWorker(paths, output_path, self.keep_toc_cb.isChecked(), self.keep_meta_cb.isChecked())
        self.worker.progress.connect(self._on_progress)
        self.worker.success.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_open_output(self):
        path = self._build_output_path()
        if os.path.exists(path):
            try:
                os.startfile(path)
            except Exception as e:
                QMessageBox.warning(self, "打开失败", str(e))
        else:
            QMessageBox.information(self, "提示", "当前尚未生成输出文件或路径不存在")

    def _on_progress(self, pct: int, msg: str):
        self.progress.setValue(max(0, min(100, int(pct))))
        self.status_label.setText(msg)

    def _on_success(self, path: str):
        self.progress.setValue(100)
        self.status_label.setText("合并完成")
        self._set_controls_enabled(True)
        QMessageBox.information(self, "成功", f"已生成合并文件:\n{path}")

    def _on_failed(self, err: str):
        self._set_controls_enabled(True)
        self.status_label.setText("合并失败")
        QMessageBox.critical(self, "失败", err)

    def _set_controls_enabled(self, enabled: bool):
        for w in (
            self.files_list,
            self.btn_merge,
            self.btn_open,
            self.output_dir_edit,
            self.output_name_edit,
        ):
            w.setEnabled(enabled)

    # ---- 拖放（外部文件）支持 ----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = []
        for u in urls:
            p = u.toLocalFile()
            if p:
                paths.append(p)
        if paths:
            self._add_paths(paths)
            event.acceptProposedAction()
        else:
            event.ignore()


def main():
    # 高分屏适配
    try:
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    except Exception:
        pass

    app = QApplication(sys.argv)
    w = PDFMergeWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()