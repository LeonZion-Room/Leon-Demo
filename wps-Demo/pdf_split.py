#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LZ-PDF 拆分 GUI（PyQt5，无系统标题栏）

功能与界面分离：
- 功能层：split_pdf、compute_smart_split_points、render_page_image、get_pdf_page_count。
- 界面层：PDFSplitWindow（无标题栏、拖拽移动、深色简洁样式）。

依赖：PyQt5、PyMuPDF。
"""

import os
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QEvent, QSize, QTimer
from PySide6.QtGui import QFont, QPixmap, QImage
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
    QScrollArea,
    QStyle,
    QFrame,
    QLineEdit,
    QFormLayout,
    QSizePolicy,
    QInputDialog,
)
from PySide6.QtGui import QCursor
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from ui_style_nb import build_style, compute_scale, dp


# -----------------------------
# 功能层
# -----------------------------

def get_pdf_page_count(pdf_path: str) -> int:
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


def render_page_image(pdf_path: str, page_index: int, zoom: float = 1.4) -> QImage:
    doc = fitz.open(pdf_path)
    page = doc[page_index]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
    doc.close()
    return img.copy()


def compute_smart_split_points(total_pages: int) -> List[int]:
    if total_pages <= 5:
        pts = [total_pages // 2] if total_pages > 2 else []
    elif total_pages <= 20:
        pts = [total_pages // 3, 2 * total_pages // 3]
    else:
        pts = list(range(10, total_pages, 10))
    return [p for p in pts if 1 <= p < total_pages]


def split_pdf(
    input_pdf_path: str,
    split_points: Optional[List[int]] = None,
    output_folder: Optional[str] = None,
    custom_names: Optional[List[str]] = None,
) -> List[str]:
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"文件不存在: {input_pdf_path}")

    doc = fitz.open(input_pdf_path)
    total_pages = len(doc)

    points = sorted(set(split_points or []))
    points = [p for p in points if 1 <= p < total_pages]

    segments: List[Tuple[int, int]] = []
    start = 0
    for p in points:
        segments.append((start, p - 1))
        start = p
    segments.append((start, total_pages - 1))

    if output_folder is None:
        output_folder = os.path.dirname(input_pdf_path)

    os.makedirs(output_folder, exist_ok=True)

    base = os.path.splitext(os.path.basename(input_pdf_path))[0]
    outputs: List[str] = []
    for i, (s, t) in enumerate(segments, 1):
        out_name = (
            custom_names[i - 1]
            if custom_names and i - 1 < len(custom_names)
            else f"{base}_part{i}.pdf"
        )
        out_path = os.path.join(output_folder, out_name)
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=s, to_page=t)
        new_doc.save(out_path)
        new_doc.close()
        outputs.append(out_path)

    doc.close()
    return outputs


# -----------------------------
# 线程层
# -----------------------------

class SplitWorker(QThread):
    progress = Signal(int, str)
    success = Signal(list)
    failed = Signal(str)

    def __init__(self, pdf_path: str, split_points: List[int], output_folder: Optional[str], custom_names: Optional[List[str]]):
        super().__init__()
        self.pdf_path = pdf_path
        self.split_points = split_points
        self.output_folder = output_folder
        self.custom_names = custom_names

    def run(self):
        try:
            self.progress.emit(10, "准备中...")
            results = split_pdf(self.pdf_path, self.split_points, self.output_folder, self.custom_names)
            self.progress.emit(100, "完成")
            self.success.emit(results)
        except Exception as e:
            self.failed.emit(str(e))


# -----------------------------
# 界面层
# -----------------------------

class PDFSplitWindow(QWidget):
    CONTACT_URL = "https://www.example.com/"  # 可按需替换

    def __init__(self, scale: Optional[float] = None, embedded: bool = False):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())
        self.resize(dp(self.scale, 900), dp(self.scale, 600))
        self.embedded = embedded

        self.pdf_path: Optional[str] = None
        self.output_folder: Optional[str] = None
        self.split_points: List[int] = []
        self.current_page = 0
        self.total_pages = 0
        self._drag_pos: Optional[QPoint] = None
        self.fit_full_page: bool = True  # 适应视口展示整页

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
        root.setSpacing(dp(self.scale, 8))

        # 自定义标题栏
        self.title_layout = QHBoxLayout()
        self.title_layout.setSpacing(dp(self.scale, 6))
        self.title_label = QLabel("LZ-PDF 拆分")
        self.title_label.setObjectName("Title")
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch(1)
        self.btn_fit = QPushButton("适应全页")
        self.btn_fit.setCheckable(True)
        self.btn_fit.setChecked(True)
        self.btn_fit.clicked.connect(self.on_toggle_fit)
        self.btn_size = QPushButton("窗口大小")
        self.btn_size.clicked.connect(self.on_set_size)
        self.btn_full = QPushButton("全屏")
        self.btn_full.clicked.connect(self.on_toggle_fullscreen)
        style = self.style()
        # 为主要窗口按钮设置标准图标与尺寸
        self.btn_full.setIcon(style.standardIcon(QStyle.SP_TitleBarMaxButton))
        self.btn_full.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        self.btn_size.setIcon(style.standardIcon(QStyle.SP_DesktopIcon))
        self.btn_size.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        self.btn_min = QPushButton("")
        self.btn_min.setIcon(style.standardIcon(QStyle.SP_TitleBarMinButton))
        self.btn_min.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        self.btn_close = QPushButton("")
        self.btn_close.setIcon(style.standardIcon(QStyle.SP_TitleBarCloseButton))
        self.btn_close.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        # 在嵌入模式下，所有窗口控制都委托给顶层窗口
        self.btn_min.clicked.connect(lambda: (self if self.isWindow() else self.window()).showMinimized())
        self.btn_close.clicked.connect(lambda: (self if self.isWindow() else self.window()).close())
        self.title_layout.addWidget(self.btn_fit)
        self.title_layout.addWidget(self.btn_size)
        self.title_layout.addWidget(self.btn_full)
        self.title_layout.addWidget(self.btn_min)
        self.title_layout.addWidget(self.btn_close)
        root.addLayout(self.title_layout)
        # 嵌入主窗口时隐藏标题栏控件，避免与主窗口重复
        if self.embedded:
            self.title_label.hide()
            self.btn_fit.hide()
            self.btn_size.hide()
            self.btn_full.hide()
            self.btn_min.hide()
            self.btn_close.hide()

        # 嵌入使用时，为避免与主窗口按钮堆叠，隐藏最小化与关闭按钮
        if not self.isWindow():
            self.btn_min.hide()
            self.btn_close.hide()

        # 主区：左预览，右操作
        self.main_row = QHBoxLayout()
        self.main_row.setSpacing(dp(self.scale, 8))

        # 左：页面预览（统一卡片样式）
        self.left_frame = QFrame()
        self.left_frame.setObjectName("PreviewCard")
        left = QVBoxLayout(self.left_frame)
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        try:
            # 让滚动条与预览内容之间留出一点缝隙
            self.preview_area.setViewportMargins(0, 0, dp(self.scale, 6), 0)
        except Exception:
            pass
        self.preview_label = QLabel("上传 PDF 以预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_area.setWidget(self.preview_label)
        # 视口尺寸变化时重新适配
        self.preview_area.viewport().installEventFilter(self)
        left.addWidget(self.preview_area)

        self.nav = QHBoxLayout()
        self.nav.setSpacing(dp(self.scale, 6))
        self.btn_prev = QPushButton("上一页")
        self.btn_prev.setIcon(style.standardIcon(QStyle.SP_ArrowBack))
        self.btn_prev.setIconSize(QSize(dp(self.scale, 16), dp(self.scale, 16)))
        self.btn_prev.setMinimumHeight(dp(self.scale, 32))
        self.btn_next = QPushButton("下一页")
        self.btn_next.setIcon(style.standardIcon(QStyle.SP_ArrowForward))
        self.btn_next.setIconSize(QSize(dp(self.scale, 16), dp(self.scale, 16)))
        self.btn_next.setMinimumHeight(dp(self.scale, 32))
        self.btn_add_point = QPushButton("设为拆分点")
        self.btn_add_point.setMinimumHeight(dp(self.scale, 32))
        self.btn_prev.clicked.connect(self.on_prev)
        self.btn_next.clicked.connect(self.on_next)
        self.btn_add_point.clicked.connect(self.on_add_point)
        self.nav.addWidget(self.btn_prev)
        self.nav.addWidget(self.btn_next)
        self.nav.addWidget(self.btn_add_point)
        left.addLayout(self.nav)

        self.main_row.addWidget(self.left_frame, 6)

        # 右：操作按钮与拆分点列表（统一卡片样式）
        self.right_frame = QFrame()
        self.right_frame.setObjectName("PanelCard")
        right = QVBoxLayout(self.right_frame)

        self.btn_pick_pdf = QPushButton("上传文件")
        self.btn_pick_pdf.setMinimumHeight(dp(self.scale, 72))
        self.btn_pick_pdf.clicked.connect(self.on_pick_pdf)
        right.addWidget(self.btn_pick_pdf)

        # 选择后的展示：PDF 路径
        self.pdf_path_edit = QLineEdit()
        self.pdf_path_edit.setReadOnly(True)
        self.pdf_path_edit.setPlaceholderText("已选择的 PDF 路径")

        self.btn_pick_output = QPushButton("选择输出路径")
        self.btn_pick_output.setMinimumHeight(dp(self.scale, 72))
        self.btn_pick_output.clicked.connect(self.on_pick_output)
        right.addWidget(self.btn_pick_output)

        # 选择后的展示：输出文件夹
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("输出文件夹")

        # 对齐展示路径信息（统一使用表单布局）
        self.pdf_path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.output_path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        path_form = QFormLayout()
        path_form.setLabelAlignment(Qt.AlignRight)
        path_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        path_form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        path_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        path_form.setHorizontalSpacing(dp(self.scale, 8))
        path_form.setVerticalSpacing(dp(self.scale, 6))

        label_w = dp(self.scale, 90)
        lbl_pdf = QLabel("PDF路径"); lbl_pdf.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lbl_pdf.setFixedWidth(label_w)
        lbl_out = QLabel("输出路径"); lbl_out.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lbl_out.setFixedWidth(label_w)

        path_form.addRow(lbl_pdf, self.pdf_path_edit)
        path_form.addRow(lbl_out, self.output_path_edit)
        right.addLayout(path_form)

        self.points_list = QListWidget()
        right.addWidget(self.points_list, 1)

        self.list_ops = QHBoxLayout()
        self.list_ops.setSpacing(dp(self.scale, 6))
        self.btn_remove = QPushButton("删除选中")
        self.btn_smart = QPushButton("智能建议")
        self.btn_remove.clicked.connect(self.on_remove_selected)
        self.btn_smart.clicked.connect(self.on_smart)
        self.list_ops.addWidget(self.btn_remove)
        self.list_ops.addWidget(self.btn_smart)
        right.addLayout(self.list_ops)

        self.action_ops = QHBoxLayout()
        self.action_ops.setSpacing(dp(self.scale, 6))
        self.btn_split = QPushButton("开始拆分")
        self.btn_open_folder = QPushButton("打开文件夹")
        self.btn_contact = QPushButton("联系我们")
        self.btn_split.clicked.connect(self.on_start_split)
        self.btn_open_folder.clicked.connect(self.on_open_folder)
        self.btn_contact.clicked.connect(self.on_contact)
        self.action_ops.addWidget(self.btn_split)
        self.action_ops.addWidget(self.btn_open_folder)
        self.action_ops.addWidget(self.btn_contact)
        right.addLayout(self.action_ops)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setMinimumHeight(dp(self.scale, 16))
        right.addWidget(self.progress)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        right.addWidget(self.status_label)

        self.main_row.addWidget(self.right_frame, 5)
        root.addLayout(self.main_row)
        # 初始执行一次自适应重排
        QTimer.singleShot(0, self._reflow_layout)
        # 初始执行一次自适应高度，避免字体裁剪
        QTimer.singleShot(0, self._apply_responsive_sizes)
        # 每秒自动检测并重排/适配预览
        self._auto_timer = QTimer(self)
        self._auto_timer.setInterval(1000)
        self._auto_timer.timeout.connect(self._on_auto_tick)
        self._auto_timer.start()

        # 底部缩略图容器：展示多页与分隔状态
        self.thumb_area = QScrollArea()
        self.thumb_area.setWidgetResizable(True)
        self.thumb_area.setFixedHeight(dp(self.scale, 120))
        try:
            # 让滚动条与缩略图之间留出一点缝隙
            self.thumb_area.setViewportMargins(0, 0, dp(self.scale, 6), 0)
        except Exception:
            pass
        self.thumb_container = QWidget()
        self.thumb_layout = QHBoxLayout(self.thumb_container)
        self.thumb_layout.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
        self.thumb_layout.setSpacing(dp(self.scale, 6))
        self.thumb_area.setWidget(self.thumb_container)
        root.addWidget(self.thumb_area)

    def _apply_style(self):
        self.setStyleSheet(build_style(self.scale))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            self._reflow_layout()
            self._apply_responsive_sizes()
        except Exception:
            pass

    # 无标题栏拖拽
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
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

    # 交互
    def on_pick_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择PDF文件", os.path.join(os.getcwd(), "测试材料"), "PDF 文件 (*.pdf)")
        if not path:
            return
        self.pdf_path = path
        try:
            self.pdf_path_edit.setText(path)
        except Exception:
            pass
        self.total_pages = get_pdf_page_count(path)
        self.current_page = 0
        self.split_points.clear()
        self.points_list.clear()
        self.status_label.setText(f"已选择: {os.path.basename(path)}，共 {self.total_pages} 页")
        self._update_preview()
        self.btn_pick_pdf.setText(os.path.basename(path))
        self.output_folder = os.path.dirname(path)
        self.btn_pick_output.setText(self.output_folder)
        try:
            self.output_path_edit.setText(self.output_folder)
        except Exception:
            pass
        self._build_thumbnails()

    def on_pick_output(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹", self.output_folder or os.getcwd())
        if folder:
            self.output_folder = folder
            self.btn_pick_output.setText(folder)
            try:
                self.output_path_edit.setText(folder)
            except Exception:
                pass

    def on_prev(self):
        if not self.pdf_path:
            return
        if self.current_page > 0:
            self.current_page -= 1
            self._update_preview()

    def on_next(self):
        if not self.pdf_path:
            return
        if self.current_page + 1 < self.total_pages:
            self.current_page += 1
            self._update_preview()

    def on_add_point(self):
        if not self.pdf_path:
            return
        p = self.current_page + 1
        if 1 <= p < self.total_pages and p not in self.split_points:
            self.split_points.append(p)
            self.split_points.sort()
            self._refresh_points_list()
            self._refresh_thumbnails()

    def on_remove_selected(self):
        item = self.points_list.currentItem()
        if not item:
            return
        val = int(item.text())
        self.split_points = [p for p in self.split_points if p != val]
        self._refresh_points_list()
        self._refresh_thumbnails()

    def on_smart(self):
        if not self.pdf_path:
            QMessageBox.information(self, "提示", "请先选择PDF文件")
            return
        pts = compute_smart_split_points(self.total_pages)
        if not pts:
            QMessageBox.information(self, "提示", "页数较少，无需拆分")
            return
        self.split_points = pts
        self._refresh_points_list()
        self._refresh_thumbnails()
        QMessageBox.information(self, "智能建议", f"建议拆分点: {pts}\n将生成 {len(pts)+1} 个文件")

    def on_start_split(self):
        if not self.pdf_path:
            QMessageBox.information(self, "提示", "请先选择PDF文件")
            return
        self.progress.setValue(0)
        self.status_label.setText("正在拆分...")
        self._set_controls(False)
        self.worker = SplitWorker(self.pdf_path, self.split_points, self.output_folder, None)
        self.worker.progress.connect(self._on_progress)
        self.worker.success.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def on_open_folder(self):
        if self.output_folder and os.path.exists(self.output_folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_folder))

    def on_contact(self):
        QDesktopServices.openUrl(QUrl(self.CONTACT_URL))

    # 辅助
    def _update_preview(self):
        if not self.pdf_path:
            return
        img = render_page_image(self.pdf_path, self.current_page)
        pix = QPixmap.fromImage(img)
        if self.fit_full_page:
            viewport = self.preview_area.viewport().size()
            if pix.isNull() or viewport.width() <= 0 or viewport.height() <= 0:
                self.preview_label.setPixmap(pix)
            else:
                scaled = pix.scaled(
                    viewport.width() - 16,
                    viewport.height() - 16,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)
        else:
            self.preview_label.setPixmap(pix)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.status_label.setText(f"第 {self.current_page+1}/{self.total_pages} 页")
        self._update_thumbnail_highlight()

    def _refresh_points_list(self):
        self.points_list.clear()
        for p in self.split_points:
            self.points_list.addItem(QListWidgetItem(str(p)))

    def _build_thumbnails(self):
        # 清理旧布局项
        while self.thumb_layout.count():
            item = self.thumb_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._thumb_labels: List[QLabel] = []
        if not self.pdf_path:
            placeholder = QLabel("请先上传 PDF")
            placeholder.setAlignment(Qt.AlignCenter)
            self.thumb_layout.addWidget(placeholder)
            return
        target_h = 90
        for i in range(self.total_pages):
            img = render_page_image(self.pdf_path, i, zoom=0.35)
            pix = QPixmap.fromImage(img)
            if not pix.isNull():
                pix = pix.scaledToHeight(target_h, Qt.SmoothTransformation)
            lbl = QLabel()
            lbl.setObjectName("thumb")
            lbl.setProperty("current", "false")
            lbl.setPixmap(pix)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(target_h + 8)
            lbl.mousePressEvent = self._make_thumb_click(i)  # 轻量绑定
            self._thumb_labels.append(lbl)
            self.thumb_layout.addWidget(lbl)
            # 如果该位置为拆分点，添加分隔条（在页后）
            if (i + 1) in self.split_points:
                sep = self._create_separator()
                self.thumb_layout.addWidget(sep)
        self._update_thumbnail_highlight()

    def _refresh_thumbnails(self):
        # 仅重绘分隔符与高亮，避免重复渲染图片
        if not hasattr(self, "_thumb_labels"):
            return
        # 先移除所有分隔条
        to_remove = []
        for idx in range(self.thumb_layout.count()):
            item = self.thumb_layout.itemAt(idx)
            w = item.widget()
            if isinstance(w, QLabel) and w.objectName() == "thumb":
                continue
            if w:
                to_remove.append(w)
        for w in to_remove:
            self.thumb_layout.removeWidget(w)
            w.deleteLater()
        # 重新插入分隔条
        label_indices = []
        for idx in range(self.thumb_layout.count()):
            w = self.thumb_layout.itemAt(idx).widget()
            if isinstance(w, QLabel) and w.objectName() == "thumb":
                label_indices.append(idx)
        # 在对应页后插入分隔条
        # 计算“页后”的布局索引偏移：分隔条会改变后续索引，因此遍历从后往前更安全
        for p in sorted(self.split_points, reverse=True):
            page_widget_index = label_indices[p - 1] if 1 <= p <= len(label_indices) else None
            if page_widget_index is None:
                continue
            sep = self._create_separator()
            self.thumb_layout.insertWidget(page_widget_index + 1, sep)
        self._update_thumbnail_highlight()

    def _update_thumbnail_highlight(self):
        if not hasattr(self, "_thumb_labels"):
            return
        for i, lbl in enumerate(self._thumb_labels):
            lbl.setProperty("current", "true" if i == self.current_page else "false")
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

    def _create_separator(self):
        # 复合分隔组件：顶部文字“拆分点” + 鲜明竖条
        sep_wrap = QWidget()
        sep_wrap.setObjectName("sep")
        sep_wrap.setFixedHeight(dp(self.scale, 90))
        sep_wrap.setFixedWidth(dp(self.scale, 26))
        v = QVBoxLayout(sep_wrap)
        v.setContentsMargins(dp(self.scale, 3), dp(self.scale, 4), dp(self.scale, 3), dp(self.scale, 4))
        v.setSpacing(dp(self.scale, 4))

        tag = QLabel("拆分点")
        tag.setObjectName("sepTag")
        tag.setAlignment(Qt.AlignCenter)
        tag.setFixedHeight(dp(self.scale, 18))

        bar = QFrame()
        bar.setObjectName("sepBar")
        bar.setFrameShape(QFrame.NoFrame)
        bar.setFixedWidth(dp(self.scale, 10))
        bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        v.addWidget(tag)
        v.addWidget(bar, 1)

        # 局部样式：使用高对比红色强调分隔
        sep_wrap.setStyleSheet(
            f"""
            QWidget#sep { background: transparent; }
            QLabel#sepTag {
                color: #EA4335;
                font-weight: 700;
                font-size: {dp(self.scale, 12)}px;
            }
            QFrame#sepBar {
                background-color: #EA4335;
                border-radius: {dp(self.scale, 3)}px;
             }
            """
        )

        return sep_wrap

    def _make_thumb_click(self, page_index: int):
        def handler(event):
            if event.button() == Qt.LeftButton:
                self.current_page = page_index
                self._update_preview()
        return handler

    # 视口尺寸改变时适配
    def eventFilter(self, obj, event):
        if obj == self.preview_area.viewport() and event.type() == QEvent.Resize:
            if self.pdf_path and self.fit_full_page:
                self._update_preview()
        return super().eventFilter(obj, event)

    def _on_auto_tick(self):
        # 周期性自检：布局重排 + 预览适配
        try:
            self._reflow_layout()
            self._apply_responsive_sizes()
        except Exception:
            pass
        if getattr(self, 'fit_full_page', True) and self.pdf_path:
            # 仅当视口尺寸发生变化时重绘，避免不必要的渲染
            vp = self.preview_area.viewport().size()
            if not hasattr(self, '_last_vp') or self._last_vp != vp:
                self._last_vp = QSize(vp.width(), vp.height())
                self._update_preview()

    def _reflow_layout(self):
        # 根据可用宽度在左右并排与上下堆叠之间切换，同时在拥挤时让行布局垂直堆叠
        try:
            root_m = self.layout().contentsMargins()
            avail_w = max(1, self.width() - (root_m.left() + root_m.right()))

            # 标题行：拥挤则改为纵向
            need_title_w = self._sum_layout_min_width(self.title_layout)
            self.title_layout.setDirection(QBoxLayout.LeftToRight if need_title_w <= avail_w else QBoxLayout.TopToBottom)

            # 主区左右卡片：根据需要切换为上下堆叠
            spacing = self.main_row.spacing()
            need_center_w = self.left_frame.sizeHint().width() + self.right_frame.sizeHint().width() + spacing
            self.main_row.setDirection(QBoxLayout.LeftToRight if need_center_w <= avail_w else QBoxLayout.TopToBottom)

            # 子行：过挤时纵向堆叠
            for row in (self.nav, self.list_ops, self.action_ops):
                need_w = self._sum_layout_min_width(row)
                row.setDirection(QBoxLayout.LeftToRight if need_w <= self.right_frame.width() else QBoxLayout.TopToBottom)
        except Exception:
            pass

    def _sum_layout_min_width(self, layout: QBoxLayout) -> int:
        # 估算布局中所有部件的最小总宽度（含间距），用于拥挤检测
        try:
            total = 0
            count = layout.count()
            spacing = layout.spacing() if hasattr(layout, 'spacing') else 0
            for i in range(count):
                item = layout.itemAt(i)
                if item and item.widget():
                    w = item.widget()
                    mw = max(1, w.minimumSizeHint().width())
                    total += mw
                    if i < count - 1:
                        total += spacing
            return total
        except Exception:
            return 0

    def _calc_size_factor(self) -> float:
        """根据右侧操作面板的可用空间计算高度缩放因子。
        在空间不足时略微压缩控件高度；空间充裕时保持或小幅增大。
        """
        try:
            base_w = max(1, dp(self.scale, 420))
            panel_w = max(1, self.right_frame.width())
            factor_w = panel_w / float(base_w)

            lay = self.right_frame.layout()
            need_h = 0
            if lay is not None:
                for i in range(lay.count()):
                    it = lay.itemAt(i)
                    w = it.widget()
                    l = it.layout()
                    s = it.spacerItem()
                    if w is not None:
                        need_h += w.minimumSizeHint().height()
                    elif l is not None:
                        need_h += l.minimumSize().height()
                    elif s is not None:
                        need_h += s.sizeHint().height()
                need_h += max(0, lay.count() - 1) * lay.spacing()
                m = lay.contentsMargins()
                need_h += m.top() + m.bottom()
            else:
                need_h = dp(self.scale, 640)

            avail_h = max(1, self.right_frame.height())
            ratio_h = min(1.0, avail_h / float(max(1, need_h)))

            f = (factor_w * 0.6 + ratio_h * 0.4)
            return max(0.55, min(1.15, f))
        except Exception:
            return 1.0

    def _apply_responsive_sizes(self):
        """为常用控件设置最小高度，并以字体度量作下限防止裁剪。"""
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

            # 顶部导航按钮
            for w, b in (
                (self.btn_prev, 32),
                (self.btn_next, 32),
                (self.btn_fit, 32),
                (self.btn_full, 32),
                (self.btn_set_size, 32),
            ):
                ensure_h(w, b)

            # 路径表单
            ensure_h(self.path_edit, 32)
            ensure_h(self.output_edit, 32)

            # 列表操作与动作操作按钮
            for w, b in (
                (self.btn_remove, 32),
                (self.btn_smart, 32),
                (self.btn_split, 36),
                (self.btn_open_folder, 36),
                (self.btn_contact, 36),
            ):
                ensure_h(w, b)

            # 进度与状态
            ensure_h(self.progress, 22, extra=6)
            ensure_h(self.status_label, 24, extra=4)

            # 列表与预览最小尺寸
            self.points_list.setMinimumHeight(H(120))
            a4w, a4h = dp(self.scale, 320), dp(self.scale, 452)
            self.preview_label.setMinimumSize(int(a4w * f), int(a4h * f))
        except Exception:
            pass

    def on_toggle_fit(self):
        self.fit_full_page = self.btn_fit.isChecked()
        self._update_preview()

    def on_toggle_fullscreen(self):
        # 顶层窗口全屏/还原切换（嵌入时作用于主窗口）
        top = self if self.isWindow() else self.window()
        if top.isFullScreen():
            top.showNormal()
            if hasattr(self, "btn_full"):
                self.btn_full.setText("全屏")
        else:
            top.showFullScreen()
            if hasattr(self, "btn_full"):
                self.btn_full.setText("还原")

    def on_set_size(self):
        top = self if self.isWindow() else self.window()
        w, ok1 = QInputDialog.getInt(self, "设置宽度", "宽度(px):", top.width(), 800, 3840, 10)
        if not ok1:
            return
        h, ok2 = QInputDialog.getInt(self, "设置高度", "高度(px):", top.height(), 600, 2160, 10)
        if not ok2:
            return
        top.resize(w, h)

    def _on_progress(self, pct: int, msg: str):
        self.progress.setValue(max(0, min(100, int(pct))))
        self.status_label.setText(msg)

    def _on_success(self, files: List[str]):
        self._set_controls(True)
        self.progress.setValue(100)
        names = "\n".join([os.path.basename(f) for f in files])
        QMessageBox.information(self, "拆分完成", f"成功生成 {len(files)} 个文件:\n\n{names}")
        self.status_label.setText("拆分完成")

    def _on_failed(self, err: str):
        self._set_controls(True)
        QMessageBox.critical(self, "失败", err)
        self.status_label.setText("拆分失败")

    def _set_controls(self, enabled: bool):
        for w in (
            self.btn_prev,
            self.btn_next,
            self.btn_add_point,
            self.btn_pick_pdf,
            self.btn_pick_output,
            self.btn_remove,
            self.btn_smart,
            self.btn_split,
            self.btn_open_folder,
            self.btn_contact,
        ):
            w.setEnabled(enabled)


def main():
    from PySide6 import QtCore
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication([])
    w = PDFSplitWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()