#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 转图片 - PyQt5 无边框美化窗口

需求实现：
- 上传PDF并按页转为图片（PNG/JPEG），按顺序输出
- 底部显示文件转换进度条
- “联系我们”点击后打开指定网站
- 无窗口顶栏（Frameless）样式，提供自定义最小化与关闭按钮
- 结构清晰：功能函数与界面代码分离，便于其他项目调用

依赖：
- PyMuPDF (fitz): pip install pymupdf
- Pillow (PIL):   pip install pillow
- PyQt5:          pip install PyQt5
"""

import os
import io
import sys
from typing import Callable, Optional

import fitz  # PyMuPDF
from PIL import Image

# ---- 可配置：联系网址 ----
CONTACT_URL = 'https://example.com/'  # 请替换为你的官网或联系页面


# ----------------- 功能函数（可被其他项目直接调用） -----------------
def _ensure_jpeg_rgb(img: Image.Image) -> Image.Image:
    """确保保存为JPEG时为RGB模式，并正确处理透明通道。"""
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        alpha = img.split()[-1] if img.mode == 'RGBA' else None
        background.paste(img, mask=alpha)
        return background
    if img.mode != 'RGB':
        return img.convert('RGB')
    return img


def convert_pdf_to_images(
    input_pdf_path: str,
    output_format: str = 'PNG',
    zoom: float = 2.0,
    output_dir: Optional[str] = None,
    prefix: str = 'page_',
    quality: int = 95,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    target_height_px: Optional[int] = None,
) -> str:
    """
    将 PDF 的每一页转换为图片并保存到输出文件夹。

    Args:
        input_pdf_path: PDF 文件路径。
        output_format: 输出图片格式，'PNG' 或 'JPEG'/'JPG'。
        zoom: 缩放因子（渲染矩阵），影响图片清晰度与大小。
        output_dir: 输出目录；默认在PDF同目录下创建同名文件夹。
        prefix: 输出文件前缀（默认 'page_'）。
        quality: JPEG 质量（1-100，有效于JPEG）。
        progress_cb: 进度回调 (pct: 0-100, msg: str)。

    Returns:
        输出文件夹路径（始终返回路径，出错会抛异常）。
    """

    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {input_pdf_path}")
    if not input_pdf_path.lower().endswith('.pdf'):
        raise ValueError("输入文件必须是PDF格式")

    output_format = output_format.upper()
    if output_format not in ('PNG', 'JPEG', 'JPG'):
        raise ValueError("不支持的图片格式，仅支持: PNG, JPEG, JPG")

    if quality < 1 or quality > 100:
        raise ValueError("JPEG质量参数应为 1-100")

    input_dir = os.path.dirname(input_pdf_path)
    input_filename = os.path.basename(input_pdf_path)
    name_without_ext = os.path.splitext(input_filename)[0]
    if output_dir is None:
        output_dir = os.path.join(input_dir, name_without_ext)
    os.makedirs(output_dir, exist_ok=True)

    # 打开PDF
    doc = fitz.open(input_pdf_path)
    total_pages = len(doc)
    pad_len = max(2, len(str(total_pages)))

    try:
        for page_num in range(total_pages):
            page = doc[page_num]
            # 若设置了目标高度，则每页自适应计算缩放
            if target_height_px and target_height_px > 0:
                page_h_pt = float(page.rect.height)
                # 基于 1:1 点到像素的 PyMuPDF 渲染逻辑，zoom 为缩放因子
                z = max(0.1, float(target_height_px) / page_h_pt)
                mat = fitz.Matrix(z, z)
            else:
                mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # 文件名与扩展名
            page_number = str(page_num + 1).zfill(pad_len)
            ext = 'jpg' if output_format in ('JPEG', 'JPG') else 'png'
            output_filename = f"{prefix}{page_number}.{ext}"
            output_path = os.path.join(output_dir, output_filename)

            # 将pixmap转换为PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # 保存
            if ext == 'jpg':
                img = _ensure_jpeg_rgb(img)
                img.save(output_path, format='JPEG', quality=int(quality), optimize=True)
            else:
                img.save(output_path, format='PNG', optimize=True)

            if progress_cb:
                try:
                    pct = (page_num + 1) * 100.0 / total_pages
                    progress_cb(pct, f"保存 {output_filename}")
                except Exception:
                    pass

            pix = None
    finally:
        try:
            doc.close()
        except Exception:
            pass

    return output_dir


# ----------------- 界面代码（PyQt5） -----------------
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QUrl, QSize, QTimer
from PySide6.QtGui import QIcon, QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QDoubleSpinBox, QSpinBox, QLineEdit, QProgressBar,
    QFrame, QSpacerItem, QSizePolicy, QMessageBox, QTextEdit, QStyle, QFormLayout,
    QBoxLayout, QSplitter,
)
from PySide6.QtGui import QDesktopServices
from ui_style_nb import build_style, compute_scale, dp


APP_STYLE = None


class ClickableLabel(QLabel):
    def __init__(self, text='', url: str = '', parent=None):
        super().__init__(text, parent)
        self.url = url
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.url:
            QDesktopServices.openUrl(QUrl(self.url))


class ConvertWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, pdf_path: str, output_format: str, zoom: float,
                 output_dir: Optional[str], prefix: str, quality: int,
                 target_height_px: Optional[int] = None):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_format = output_format
        self.zoom = zoom
        self.output_dir = output_dir
        self.prefix = prefix
        self.quality = quality
        self.target_height_px = target_height_px

    def run(self):
        try:
            def cb(pct, msg):
                self.progress.emit(int(pct), str(msg))

            out_dir = convert_pdf_to_images(
                input_pdf_path=self.pdf_path,
                output_format=self.output_format,
                zoom=self.zoom,
                output_dir=self.output_dir,
                prefix=self.prefix,
                quality=self.quality,
                progress_cb=cb,
                target_height_px=self.target_height_px,
            )
            self.finished.emit(out_dir)
        except Exception as e:
            self.failed.emit(str(e))


class PdfToImagesWindow(QWidget):
    def __init__(self, scale: Optional[float] = None, embedded: bool = False):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())
        self.embedded = embedded
        self.setMinimumSize(dp(self.scale, 840), dp(self.scale, 520))
        self.drag_pos: Optional[QPoint] = None

        # 预览/状态
        self.doc: Optional[fitz.Document] = None
        self.total_pages: int = 0
        self.current_page_index: int = 0
        self.fit_to_window: bool = True
        self.preview_scale: float = 1.0
        self.is_fullscreen: bool = False
        # A4 纵向比例（宽/高 = 210/297 ≈ 0.7071）
        self.preview_aspect_w_over_h: float = 210.0 / 297.0

        self.setStyleSheet(build_style(self.scale))
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
            self.drag_pos = event.globalPos() - top.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() & Qt.LeftButton:
            top = self if self.isWindow() else self.window()
            top.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
        root.setSpacing(dp(self.scale, 8))

        # 顶部标题 + 控件
        self.title_bar = QFrame(self)
        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
        self.title_layout.setSpacing(dp(self.scale, 6))

        title = QLabel("LZ-PDF 转图片")
        title.setObjectName("Title")
        self.title_layout.addWidget(title)
        self.title_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        btn_fit = QPushButton("适应全文")
        btn_fit.clicked.connect(self._toggle_fit_to_window)
        btn_fit.setMinimumHeight(dp(self.scale, 32))
        self.title_layout.addWidget(btn_fit)

        btn_resize = QPushButton("窗口大小")
        btn_resize.clicked.connect(self._cycle_window_size)
        btn_resize.setMinimumHeight(dp(self.scale, 32))
        self.title_layout.addWidget(btn_resize)

        btn_full = QPushButton("全屏")
        btn_full.clicked.connect(self._toggle_fullscreen)
        btn_full.setMinimumHeight(dp(self.scale, 32))
        self.title_layout.addWidget(btn_full)

        # 标准窗口控制图标
        style = self.style()
        # 为主要窗口按钮设置图标尺寸
        btn_full.setIcon(style.standardIcon(QStyle.SP_TitleBarMaxButton))
        btn_full.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_resize.setIcon(style.standardIcon(QStyle.SP_DesktopIcon))
        btn_resize.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))

        # 联系我们按钮放在同一行
        btn_contact_top = QPushButton("联系我们")
        btn_contact_top.setMinimumHeight(dp(self.scale, 32))
        btn_contact_top.setIcon(style.standardIcon(QStyle.SP_DialogHelpButton))
        btn_contact_top.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_contact_top.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(CONTACT_URL)))
        self.title_layout.addWidget(btn_contact_top)

        btn_min = QPushButton("")
        btn_min.setIcon(style.standardIcon(QStyle.SP_TitleBarMinButton))
        btn_min.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_min.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
        btn_min.clicked.connect(lambda: (self if self.isWindow() else self.window()).showMinimized())
        self.title_layout.addWidget(btn_min)

        btn_close = QPushButton("")
        btn_close.setIcon(style.standardIcon(QStyle.SP_TitleBarCloseButton))
        btn_close.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        btn_close.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
        btn_close.clicked.connect(lambda: (self if self.isWindow() else self.window()).close())
        self.title_layout.addWidget(btn_close)

        # 嵌入在主窗口时，隐藏自身的最小化/关闭按钮，避免与主窗口控制重复堆叠
        if not self.isWindow():
            btn_min.hide()
            btn_close.hide()

        root.addWidget(self.title_bar)
        # 嵌入主窗口时不展示子页面标题栏，避免视觉重复与不协调
        if self.embedded:
            self.title_bar.hide()

        # 中间主体区域：左预览 + 右控制（改为 QSplitter 可拖拽分割）
        self.main_splitter = QSplitter(Qt.Horizontal)
        try:
            self.main_splitter.setHandleWidth(dp(self.scale, 6))
        except Exception:
            pass

        # 左：预览卡片
        self.preview_card = QFrame(self)
        self.preview_card.setObjectName("PreviewCard")
        self.preview_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout = QVBoxLayout(self.preview_card)
        preview_layout.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))

        self.preview_label = QLabel("上传 PDF 以预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        # 预览区域最小尺寸按 A4 比例（约 320x452）
        self.preview_label.setMinimumSize(dp(self.scale, 320), dp(self.scale, 452))
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_layout.addWidget(self.preview_label)

        # 底部：页导航
        self.nav_row = QHBoxLayout()
        self.nav_row.setSpacing(dp(self.scale, 6))
        self.btn_prev = QPushButton("上一页")
        self.btn_prev.setIcon(style.standardIcon(QStyle.SP_ArrowBack))
        self.btn_prev.setIconSize(QSize(dp(self.scale, 16), dp(self.scale, 16)))
        self.btn_prev.setMinimumHeight(dp(self.scale, 32))
        self.btn_prev.clicked.connect(self._prev_page)
        self.btn_next = QPushButton("下一页")
        self.btn_next.setIcon(style.standardIcon(QStyle.SP_ArrowForward))
        self.btn_next.setIconSize(QSize(dp(self.scale, 16), dp(self.scale, 16)))
        self.btn_next.setMinimumHeight(dp(self.scale, 32))
        self.btn_next.clicked.connect(self._next_page)
        self.nav_row.addWidget(self.btn_prev)
        self.nav_row.addWidget(self.btn_next)
        preview_layout.addLayout(self.nav_row)

        self.main_splitter.addWidget(self.preview_card)

        # 右：控制卡片
        self.panel_card = QFrame(self)
        self.panel_card.setObjectName("PanelCard")
        self.panel_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        panel_layout = QVBoxLayout(self.panel_card)
        panel_layout.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))
        panel_layout.setSpacing(dp(self.scale, 8))

        # 文件选择 + 输出
        self.pdf_path_edit = QLineEdit()
        self.pdf_path_edit.setPlaceholderText("上传文件后左侧可预览")
        self.pdf_path_edit.setReadOnly(True)
        self.pdf_path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.pdf_path_edit.setMinimumHeight(dp(self.scale, 32))
        btn_choose_pdf = QPushButton("上传文件")
        btn_choose_pdf.clicked.connect(self._choose_pdf)
        btn_choose_pdf.setMinimumHeight(dp(self.scale, 32))

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("选择输出路径（默认：PDF同名文件夹）")
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.output_dir_edit.setMinimumHeight(dp(self.scale, 32))
        btn_choose_out = QPushButton("选择输出路径")
        btn_choose_out.clicked.connect(self._choose_output_dir)
        btn_choose_out.setMinimumHeight(dp(self.scale, 32))

        panel_layout.addWidget(btn_choose_pdf)
        panel_layout.addWidget(self.pdf_path_edit)
        panel_layout.addWidget(btn_choose_out)
        panel_layout.addWidget(self.output_dir_edit)

        # 删除无用的拆分点列表与相关操作，简化界面

        # 参数（统一表单布局，更易对齐与阅读）
        params_form = QFormLayout()
        params_form.setLabelAlignment(Qt.AlignRight)
        params_form.setFormAlignment(Qt.AlignLeft)
        params_form.setHorizontalSpacing(dp(self.scale, 8))
        params_form.setVerticalSpacing(dp(self.scale, 6))
        try:
            # 让所有非固定字段在容器变宽时自动拉伸，达到“填满容器”的效果
            params_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        except Exception:
            pass
        try:
            # 行宽不足时自动把标签与字段换到两行，避免超出容器
            params_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        except Exception:
            pass

        self.format_combo = QComboBox(); self.format_combo.addItems(["PNG", "JPEG"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.format_combo.setMinimumHeight(dp(self.scale, 32))
        self.zoom_spin = QDoubleSpinBox(); self.zoom_spin.setRange(0.5, 5.0); self.zoom_spin.setSingleStep(0.5); self.zoom_spin.setValue(2.0); self.zoom_spin.setSuffix("x")
        self.zoom_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.zoom_spin.setMinimumHeight(dp(self.scale, 32))
        self.height_spin = QSpinBox(); self.height_spin.setRange(0, 20000); self.height_spin.setValue(1600); self.height_spin.setSuffix(" px"); self.height_spin.setSpecialValueText("按缩放")
        self.height_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.height_spin.setMinimumHeight(dp(self.scale, 32))
        self.quality_spin = QSpinBox(); self.quality_spin.setRange(1, 100); self.quality_spin.setValue(95); self.quality_spin.setEnabled(self.format_combo.currentText() == 'JPEG')
        self.quality_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.quality_spin.setMinimumHeight(dp(self.scale, 32))
        self.prefix_edit = QLineEdit("page_")
        self.prefix_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.prefix_edit.setMinimumHeight(dp(self.scale, 32))

        lab_format = QLabel("格式"); lab_format.setWordWrap(True)
        lab_zoom = QLabel("缩放"); lab_zoom.setWordWrap(True)
        lab_height = QLabel("导出高度(px)"); lab_height.setWordWrap(True)
        lab_quality = QLabel("JPEG质量"); lab_quality.setWordWrap(True)
        lab_prefix = QLabel("文件前缀"); lab_prefix.setWordWrap(True)

        params_form.addRow(lab_format, self.format_combo)
        params_form.addRow(lab_zoom, self.zoom_spin)
        params_form.addRow(lab_height, self.height_spin)
        params_form.addRow(lab_quality, self.quality_spin)
        params_form.addRow(lab_prefix, self.prefix_edit)
        panel_layout.addLayout(params_form)

        # 底部：转换/打开/联系
        self.action_row = QHBoxLayout()
        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.clicked.connect(self._start_convert)
        self.btn_convert.setMinimumHeight(dp(self.scale, 36))
        self.btn_open_out = QPushButton("打开文件夹")
        self.btn_open_out.clicked.connect(self._open_output_folder)
        self.btn_open_out.setEnabled(False)
        self.btn_open_out.setMinimumHeight(dp(self.scale, 36))
        self.action_row.addWidget(self.btn_convert)
        self.action_row.addWidget(self.btn_open_out)
        panel_layout.addLayout(self.action_row)

        self.main_splitter.addWidget(self.panel_card)
        try:
            self.main_splitter.setCollapsible(0, False)
            self.main_splitter.setCollapsible(1, False)
            self.main_splitter.setStretchFactor(0, 3)
            self.main_splitter.setStretchFactor(1, 2)
        except Exception:
            pass
        root.addWidget(self.main_splitter)

        # 进度 + 日志
        self.log_card = QFrame(self)
        self.log_card.setObjectName("LogCard")
        self.log_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        log_layout = QVBoxLayout(self.log_card)
        log_layout.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))

        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0, 100); self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(dp(self.scale, 22))
        self.log_edit = QTextEdit(); self.log_edit.setReadOnly(True); self.log_edit.setPlaceholderText("就绪")
        self.log_edit.setMinimumHeight(dp(self.scale, 160))
        log_layout.addWidget(self.progress_bar)
        log_layout.addWidget(self.log_edit)
        root.addWidget(self.log_card)
        # 初始进行一次自适应重排
        QTimer.singleShot(0, self._reflow_layout)
        QTimer.singleShot(0, self._apply_responsive_sizes)
        # 每秒自动检测并重排
        self._auto_timer = QTimer(self)
        self._auto_timer.setInterval(1000)
        self._auto_timer.timeout.connect(self._reflow_layout)
        self._auto_timer.start()

        self.out_dir_last: Optional[str] = None

    def _on_format_changed(self, text: str):
        self.quality_spin.setEnabled(text.upper() == 'JPEG')

    def _choose_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择PDF文件", os.getcwd(), "PDF 文件 (*.pdf)")
        if path:
            self.pdf_path_edit.setText(path)
            try:
                self._open_doc(path)
                self.log_edit.append(f"已加载：{os.path.basename(path)}，共 {self.total_pages} 页")
            except Exception as e:
                QMessageBox.critical(self, "失败", f"打开PDF失败：{e}")

    def _choose_output_dir(self):
        dir_ = QFileDialog.getExistingDirectory(self, "选择输出目录", os.getcwd())
        if dir_:
            self.output_dir_edit.setText(dir_)

    def _open_output_folder(self):
        if self.out_dir_last and os.path.exists(self.out_dir_last):
            try:
                if os.name == 'nt':
                    os.startfile(self.out_dir_last)
                elif sys.platform == 'darwin':
                    import subprocess
                    subprocess.run(['open', self.out_dir_last], check=False)
                else:
                    import subprocess
                    subprocess.run(['xdg-open', self.out_dir_last], check=False)
            except Exception:
                QMessageBox.information(self, "提示", f"请手动打开文件夹：{self.out_dir_last}")
        else:
            QMessageBox.information(self, "提示", "暂未生成输出或目录不存在")

    def _start_convert(self):
        pdf_path = self.pdf_path_edit.text().strip()
        if not pdf_path:
            QMessageBox.warning(self, "提示", "请先选择PDF文件")
            return
        if not os.path.exists(pdf_path):
            QMessageBox.warning(self, "提示", "所选PDF路径不存在")
            return

        output_format = self.format_combo.currentText().upper()
        zoom = float(self.zoom_spin.value())
        prefix = self.prefix_edit.text().strip() or 'page_'
        quality = int(self.quality_spin.value())
        output_dir = self.output_dir_edit.text().strip() or None

        self.btn_convert.setEnabled(False)
        self.progress_bar.setValue(0)

        height_px = int(self.height_spin.value())
        target_h = height_px if height_px > 0 else None
        self.worker = ConvertWorker(pdf_path, output_format, zoom, output_dir, prefix, quality, target_height_px=target_h)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(lambda _: self.btn_convert.setEnabled(True))
        self.worker.failed.connect(lambda _: self.btn_convert.setEnabled(True))
        self.worker.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(int(pct))
        self.log_edit.append(msg)

    def _on_finished(self, out_dir: str):
        self.out_dir_last = out_dir
        self.btn_open_out.setEnabled(True)
        QMessageBox.information(self, "完成", f"转换完成！输出目录：\n{out_dir}")

    def _on_failed(self, err: str):
        QMessageBox.critical(self, "失败", f"转换失败：{err}")

    # ----------------- 预览/导航/交互 -----------------
    def _open_doc(self, path: str):
        if self.doc:
            try:
                self.doc.close()
            except Exception:
                pass
        self.doc = fitz.open(path)
        self.total_pages = len(self.doc)
        self.current_page_index = 0
        self._update_preview()

    def _render_page(self, index: int, scale: float = 1.0) -> Optional[QPixmap]:
        if not self.doc or index < 0 or index >= self.total_pages:
            return None
        page = self.doc[index]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        qimg = img.copy()
        return QPixmap.fromImage(qimg)

    def _update_preview(self):
        pm = self._render_page(self.current_page_index, self.preview_scale)
        if pm:
            if self.fit_to_window:
                # 将目标尺寸限制为 A4 比例的最大可用区域
                avail = self.preview_label.size()
                aspect = self.preview_aspect_w_over_h  # 宽/高
                # 根据可用区域选择受限方向
                if avail.width() / max(1, avail.height()) < aspect:
                    # 受宽限制
                    target_w = max(1, avail.width())
                    target_h = int(target_w / aspect)
                    if target_h > avail.height():
                        target_h = avail.height()
                        target_w = int(target_h * aspect)
                else:
                    # 受高限制
                    target_h = max(1, avail.height())
                    target_w = int(target_h * aspect)
                    if target_w > avail.width():
                        target_w = avail.width()
                        target_h = int(target_w / aspect)
                pm = pm.scaled(QSize(target_w, target_h), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pm)
            self.preview_label.setText("")
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("上传 PDF 以预览")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.fit_to_window:
            self._update_preview()
        # 横向拥挤时自动重排为纵向堆叠
        self._reflow_layout()
        # 根据 scale 与窗口尺寸自动调整控件高度
        self._apply_responsive_sizes()

    def _prev_page(self):
        if not self.doc:
            return
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self._update_preview()

    def _next_page(self):
        if not self.doc:
            return
        if self.current_page_index < self.total_pages - 1:
            self.current_page_index += 1
            self._update_preview()

    # 删除拆分相关方法

    def _toggle_fit_to_window(self):
        self.fit_to_window = not self.fit_to_window
        self._update_preview()

    def _cycle_window_size(self):
        # 委托顶层窗口调整尺寸（嵌入模式）
        top = self if self.isWindow() else self.window()
        if self.is_fullscreen:
            return
        w, h = top.width(), top.height()
        if w < 900:
            top.resize(1080, 680)
        elif w < 1200:
            top.resize(1200, 740)
        else:
            top.resize(840, 520)
        self._update_preview()
        self._reflow_layout()

    def _sum_layout_min_width(self, layout: QHBoxLayout) -> int:
        try:
            total = 0
            for i in range(layout.count()):
                it = layout.itemAt(i)
                w = it.widget()
                if w is not None:
                    total += w.sizeHint().width()
            lm = layout.contentsMargins()
            total += layout.spacing() * max(0, layout.count() - 1) + lm.left() + lm.right()
            return total
        except Exception:
            return 0

    def _reflow_layout(self):
        try:
            # 可用宽度（根布局左右边距后）
            root = self.layout()
            m = root.contentsMargins() if root is not None else None
            avail_w = self.width()
            if m:
                avail_w -= (m.left() + m.right())

            # 顶部标题栏：拥挤则纵向堆叠
            need_title_w = self._sum_layout_min_width(self.title_layout)
            self.title_layout.setDirection(
                QBoxLayout.LeftToRight if need_title_w <= avail_w else QBoxLayout.TopToBottom
            )

            # 中部主行：根据可用宽度切换分割器方向（横向并排 / 纵向堆叠）
            need_center_w = self.preview_card.sizeHint().width() + self.panel_card.sizeHint().width() + dp(self.scale, 8)
            cm = self.layout().contentsMargins()
            avail_center_w = max(1, self.width() - (cm.left() + cm.right()))
            try:
                self.main_splitter.setOrientation(
                    Qt.Horizontal if need_center_w <= avail_center_w else Qt.Vertical
                )
            except Exception:
                pass

            # 右侧底部操作行：按钮过挤时改为纵向
            panel_w = max(self.panel_card.width(), self.panel_card.sizeHint().width())
            need_action_w = self._sum_layout_min_width(self.action_row)
            self.action_row.setDirection(
                QBoxLayout.LeftToRight if need_action_w <= panel_w else QBoxLayout.TopToBottom
            )

            # 预览导航：过挤时改为纵向
            pv_w = max(self.preview_card.width(), self.preview_card.sizeHint().width())
            need_nav_w = self._sum_layout_min_width(self.nav_row)
            self.nav_row.setDirection(
                QBoxLayout.LeftToRight if need_nav_w <= pv_w else QBoxLayout.TopToBottom
            )
        except Exception:
            pass

    def _calc_size_factor(self) -> float:
        """基于右侧面板宽度与其可用高度计算自适应缩放因子。
        目标：空间不足时自动缩短控件高度，空间充裕时略增，但限制在合理范围。
        """
        try:
            # 宽度因子：按右侧面板可用宽度与基准宽度比值
            base_w = max(1, dp(self.scale, 420))
            panel_w = max(1, self.panel_card.width())
            factor_w = panel_w / float(base_w)

            # 高度因子：按右侧面板可用高度与内容最小需求比值进行压缩
            lay = self.panel_card.layout()
            # 估算当前布局的最小竖向需求
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
                        sz = l.minimumSize()
                        need_h += sz.height()
                    elif s is not None:
                        need_h += s.sizeHint().height()
                need_h += max(0, lay.count() - 1) * lay.spacing()
                m = lay.contentsMargins()
                need_h += m.top() + m.bottom()
            else:
                need_h = dp(self.scale, 640)

            avail_h = max(1, self.panel_card.height())
            ratio_h = min(1.0, avail_h / float(max(1, need_h)))

            # 若高度不足，优先按高度比值进行更强压缩
            if avail_h < need_h:
                f = (factor_w * 0.4 + ratio_h * 0.6)
                f = min(f, ratio_h * 0.95)
            else:
                f = (factor_w * 0.6 + ratio_h * 0.4)
            return max(0.50, min(1.15, f))
        except Exception:
            return 1.0

    def _apply_responsive_sizes(self):
        """按计算因子给常用控件设置最小高度，实现随窗口变化的自适应。"""
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

            # 表单区与操作按钮
            for w in (
                self.pdf_path_edit,
                self.output_dir_edit,
                self.format_combo,
                self.zoom_spin,
                self.height_spin,
                self.quality_spin,
                self.prefix_edit,
            ):
                ensure_h(w, 32)

            ensure_h(self.btn_convert, 36)
            ensure_h(self.btn_open_out, 36)
            ensure_h(self.progress_bar, 22, extra=6)
            self.log_edit.setMinimumHeight(H(160))

            # 预览导航与预览卡片最小尺寸（保持 A4 比例，但高度随空间微调）
            ensure_h(self.btn_prev, 32)
            ensure_h(self.btn_next, 32)
            # 以 A4 比例约 320x452 作为基准，随因子变化
            a4w, a4h = dp(self.scale, 320), dp(self.scale, 452)
            self.preview_label.setMinimumSize(int(a4w * f), int(a4h * f))
        except Exception:
            pass

    def _toggle_fullscreen(self):
        # 顶层窗口全屏/还原切换（嵌入时作用于主窗口）
        top = self if self.isWindow() else self.window()
        if not top.isFullScreen():
            top.showFullScreen()
            self.is_fullscreen = True
        else:
            top.showNormal()
            self.is_fullscreen = False
        self._update_preview()


def launch_app():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF 转图片")
    win = PdfToImagesWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    launch_app()