#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
from typing import Optional, Callable, List, Tuple

import fitz  # PyMuPDF
from PIL import Image

from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QFileDialog,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QProgressBar,
    QSizePolicy,
    QFormLayout,
    QStyle,
)

from ui_style_nb import build_style, compute_scale, dp


def _ensure_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        alpha = img.split()[-1] if img.mode == "RGBA" else None
        bg.paste(img, mask=alpha)
        return bg
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def convert_pdf_to_single_image(
    input_pdf_path: str,
    output_path: str,
    output_format: str = "PNG",
    zoom: float = 2.0,
    target_width_px: Optional[int] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> str:
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {input_pdf_path}")
    if not input_pdf_path.lower().endswith(".pdf"):
        raise ValueError("输入文件必须是PDF格式")

    output_format = output_format.upper()
    if output_format not in ("PNG", "JPEG", "JPG"):
        raise ValueError("仅支持 PNG 或 JPEG 输出")

    doc = fitz.open(input_pdf_path)
    total_pages = len(doc)
    images: List[Image.Image] = []
    try:
        for i in range(total_pages):
            page = doc[i]
            if target_width_px and target_width_px > 0:
                page_w_pt = float(page.rect.width)
                scale = max(0.1, float(target_width_px) / page_w_pt)
                mat = fitz.Matrix(scale, scale)
            else:
                mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            images.append(img)
            if progress_cb:
                try:
                    progress_cb((i + 1) * 100.0 / total_pages, f"渲染第 {i+1} 页")
                except Exception:
                    pass
    finally:
        try:
            doc.close()
        except Exception:
            pass

    if not images:
        raise RuntimeError("无法从PDF渲染任何页面")

    # 统一宽度为所有页的最大宽度，按比例缩放每页后纵向拼接
    max_w = max(img.width for img in images)
    scaled: List[Image.Image] = []
    total_h = 0
    for img in images:
        if img.width != max_w:
            new_h = int(img.height * (max_w / float(img.width)))
            img = img.resize((max_w, max(1, new_h)), Image.LANCZOS)
        # 输出为 JPEG 时强制转换为 RGB
        if output_format in ("JPEG", "JPG"):
            img = _ensure_rgb(img)
        scaled.append(img)
        total_h += img.height

    mode = "RGB" if output_format in ("JPEG", "JPG") else ("RGBA" if any(im.mode == "RGBA" for im in scaled) else "RGB")
    canvas = Image.new(mode, (max_w, total_h), (255, 255, 255) if mode == "RGB" else (255, 255, 255, 0))
    y = 0
    for idx, img in enumerate(scaled, 1):
        canvas.paste(img, (0, y))
        y += img.height
        if progress_cb:
            try:
                progress_cb(70 + idx * 30.0 / len(scaled), f"拼接第 {idx} 页")
            except Exception:
                pass

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    if output_format in ("JPEG", "JPG"):
        canvas = _ensure_rgb(canvas)
        canvas.save(output_path, format="JPEG", quality=95, optimize=True)
    else:
        canvas.save(output_path, format="PNG", optimize=True)
    return output_path


class _SingleImageWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        pdf_path: str,
        output_path: str,
        fmt: str,
        zoom: float,
        target_width_px: Optional[int],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.fmt = fmt
        self.zoom = zoom
        self.target_width_px = target_width_px

    def run(self):
        try:
            def cb(pct, msg):
                self.progress.emit(int(pct))
            out = convert_pdf_to_single_image(
                input_pdf_path=self.pdf_path,
                output_path=self.output_path,
                output_format=self.fmt,
                zoom=self.zoom,
                target_width_px=self.target_width_px,
                progress_cb=cb,
            )
            self.finished.emit(out)
        except Exception as e:
            self.failed.emit(str(e))


class PdfToOneImageWindow(QWidget):
    """
    PDF 转一张图：将整份 PDF 渲染为一张纵向长图。
    参考现有 pdf2images 的风格，简化为文件选择 + 参数 + 进度。
    """

    def __init__(self, scale: Optional[float] = None, embedded: bool = False):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())
        self.embedded = embedded
        self.setMinimumSize(dp(self.scale, 840), dp(self.scale, 520))

        self.setStyleSheet(build_style(self.scale))
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
        root.setSpacing(dp(self.scale, 8))

        # 顶部标题栏（嵌入主窗口时隐藏）
        self.title_bar = QFrame(self)
        tl = QHBoxLayout(self.title_bar)
        tl.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
        tl.setSpacing(dp(self.scale, 6))
        title = QLabel("PDF 转一张图")
        tl.addWidget(title)
        tl.addStretch(1)
        style = self.style()
        self.btn_min = QPushButton("")
        self.btn_min.setIcon(style.standardIcon(QStyle.SP_TitleBarMinButton))
        self.btn_min.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        self.btn_min.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
        self.btn_min.clicked.connect(lambda: (self if self.isWindow() else self.window()).showMinimized())
        tl.addWidget(self.btn_min)
        self.btn_close = QPushButton("")
        self.btn_close.setIcon(style.standardIcon(QStyle.SP_TitleBarCloseButton))
        self.btn_close.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        self.btn_close.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
        self.btn_close.clicked.connect(lambda: (self if self.isWindow() else self.window()).close())
        tl.addWidget(self.btn_close)
        root.addWidget(self.title_bar)
        if self.embedded:
            self.title_bar.hide()

        # 控制面板
        card = QFrame(self)
        card.setObjectName("PanelCard")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))
        lay.setSpacing(dp(self.scale, 8))
        # 保存引用以便响应缩放更新
        self.panel_card = card
        self.panel_layout = lay

        self.btn_choose_pdf = QPushButton("选择PDF文件")
        self.btn_choose_pdf.setMinimumHeight(dp(self.scale, 32))
        self.btn_choose_pdf.clicked.connect(self._choose_pdf)
        self.edit_pdf = QLineEdit()
        self.edit_pdf.setMinimumHeight(dp(self.scale, 32))
        self.edit_pdf.setReadOnly(True)
        lay.addWidget(self.btn_choose_pdf)
        lay.addWidget(self.edit_pdf)

        self.btn_choose_out = QPushButton("选择输出图片")
        self.btn_choose_out.setMinimumHeight(dp(self.scale, 32))
        self.btn_choose_out.clicked.connect(self._choose_output)
        self.edit_out = QLineEdit()
        self.edit_out.setMinimumHeight(dp(self.scale, 32))
        lay.addWidget(self.btn_choose_out)
        lay.addWidget(self.edit_out)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        try:
            form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
            form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        except Exception:
            pass

        self.combo_fmt = QComboBox(); self.combo_fmt.addItems(["PNG", "JPEG"])
        self.spin_zoom = QDoubleSpinBox(); self.spin_zoom.setRange(0.5, 5.0); self.spin_zoom.setSingleStep(0.5); self.spin_zoom.setValue(2.0); self.spin_zoom.setSuffix("x")
        self.spin_width = QSpinBox(); self.spin_width.setRange(0, 20000); self.spin_width.setValue(1200); self.spin_width.setSuffix(" px"); self.spin_width.setSpecialValueText("按缩放")
        form.addRow(QLabel("格式"), self.combo_fmt)
        form.addRow(QLabel("缩放"), self.spin_zoom)
        form.addRow(QLabel("目标宽度(px)"), self.spin_width)
        lay.addLayout(form)

        row = QHBoxLayout()
        self.btn_start = QPushButton("开始转换")
        self.btn_start.setMinimumHeight(dp(self.scale, 36))
        self.btn_start.clicked.connect(self._start_convert)
        self.btn_open = QPushButton("打开输出")
        self.btn_open.setMinimumHeight(dp(self.scale, 36))
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._open_output)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_open)
        lay.addLayout(row)

        self.progress = QProgressBar(); self.progress.setRange(0, 100); self.progress.setValue(0)
        self.progress.setMinimumHeight(dp(self.scale, 22))
        self.log = QLabel(""); self.log.setWordWrap(True)
        lay.addWidget(self.progress)
        lay.addWidget(self.log)

        root.addWidget(card)

    def _apply_style(self):
        try:
            self.setStyleSheet(build_style(self.scale))
        except Exception:
            pass

    def _apply_responsive_sizes(self):
        try:
            # 根布局与标题栏
            root = self.layout()
            root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
            root.setSpacing(dp(self.scale, 8))
            if hasattr(self, 'title_bar') and self.title_bar and self.title_bar.layout():
                tl = self.title_bar.layout()
                tl.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
                tl.setSpacing(dp(self.scale, 6))
            # 标题按钮
            if hasattr(self, 'btn_min') and self.btn_min:
                self.btn_min.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
                self.btn_min.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
            if hasattr(self, 'btn_close') and self.btn_close:
                self.btn_close.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
                self.btn_close.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
            # 面板卡片与控件高度
            if hasattr(self, 'panel_layout') and self.panel_layout:
                self.panel_layout.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))
                self.panel_layout.setSpacing(dp(self.scale, 8))
            for w in (getattr(self, 'btn_choose_pdf', None), getattr(self, 'edit_pdf', None), getattr(self, 'btn_choose_out', None), getattr(self, 'edit_out', None)):
                try:
                    if w:
                        w.setMinimumHeight(dp(self.scale, 32))
                except Exception:
                    pass
            for w in (getattr(self, 'btn_start', None), getattr(self, 'btn_open', None)):
                try:
                    if w:
                        w.setMinimumHeight(dp(self.scale, 36))
                except Exception:
                    pass
            if hasattr(self, 'progress') and self.progress:
                self.progress.setMinimumHeight(dp(self.scale, 22))
        except Exception:
            pass

    # --- 交互 ---
    def _choose_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择PDF文件", os.getcwd(), "PDF 文件 (*.pdf)")
        if path:
            self.edit_pdf.setText(path)
            base = os.path.splitext(os.path.basename(path))[0]
            out_dir = os.path.dirname(path) or "."
            ext = self.combo_fmt.currentText().lower()
            self.edit_out.setText(os.path.join(out_dir, f"{base}_long.{ 'jpg' if ext=='jpeg' else 'png' }"))

    def _choose_output(self):
        fmt = self.combo_fmt.currentText().upper()
        filters = "PNG 图片 (*.png)" if fmt == "PNG" else "JPEG 图片 (*.jpg *.jpeg)"
        path, _ = QFileDialog.getSaveFileName(self, "选择输出图片", self.edit_out.text() or "output.png", filters)
        if path:
            self.edit_out.setText(path)

    def _start_convert(self):
        pdf = self.edit_pdf.text().strip()
        out = self.edit_out.text().strip()
        if not pdf:
            self.log.setText("请先选择PDF文件")
            return
        if not os.path.exists(pdf):
            self.log.setText("PDF路径不存在")
            return
        if not out:
            base = os.path.splitext(os.path.basename(pdf))[0]
            out_dir = os.path.dirname(pdf) or "."
            ext = self.combo_fmt.currentText().upper()
            out = os.path.join(out_dir, f"{base}_long.{ 'jpg' if ext=='JPEG' else 'png' }")
            self.edit_out.setText(out)

        self.btn_start.setEnabled(False)
        self.progress.setValue(0)
        self.log.setText("正在转换...")
        fmt = self.combo_fmt.currentText().upper()
        zoom = float(self.spin_zoom.value())
        width = int(self.spin_width.value())
        target_w = width if width > 0 else None
        self._worker = _SingleImageWorker(pdf, out, fmt, zoom, target_w)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.finished.connect(self._on_ok)
        self._worker.failed.connect(self._on_fail)
        self._worker.finished.connect(lambda _: self.btn_start.setEnabled(True))
        self._worker.failed.connect(lambda _: self.btn_start.setEnabled(True))
        self._worker.start()

    def _on_ok(self, path: str):
        self.log.setText(f"转换完成：{path}")
        self.btn_open.setEnabled(True)

    def _on_fail(self, msg: str):
        self.log.setText(f"转换失败：{msg}")

    def _open_output(self):
        p = self.edit_out.text().strip()
        try:
            if p and os.path.exists(p):
                # 打开生成的文件本身
                if not QDesktopServices.openUrl(QUrl.fromLocalFile(p)):
                    # 作为兜底，在 Windows 上尝试使用系统默认方式
                    try:
                        os.startfile(p)  # type: ignore[attr-defined]
                    except Exception:
                        # 退一步打开其所在目录
                        d = os.path.dirname(p)
                        if d and os.path.exists(d):
                            QDesktopServices.openUrl(QUrl.fromLocalFile(d))
        except Exception:
            try:
                # 最后兜底：打开其所在目录
                d = os.path.dirname(p)
                if d and os.path.exists(d):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(d))
            except Exception:
                pass