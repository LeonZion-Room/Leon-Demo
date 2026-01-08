#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
from typing import Optional, Callable

import fitz  # PyMuPDF
from PIL import Image

from PySide6.QtCore import Qt, QThread, Signal, QUrl, QSize
from PySide6.QtGui import QDesktopServices
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
    QDoubleSpinBox,
    QSpinBox,
    QProgressBar,
    QFormLayout,
    QStyle,
)

from ui_style_nb import build_style, compute_scale, dp


def convert_pdf_to_image_only_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    zoom: float = 2.0,
    target_height_px: Optional[int] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
) -> str:
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {input_pdf_path}")
    if not input_pdf_path.lower().endswith(".pdf"):
        raise ValueError("输入文件必须是PDF格式")

    doc = fitz.open(input_pdf_path)
    out_doc = fitz.open()
    total = len(doc)
    try:
        for i in range(total):
            page = doc[i]
            w_pt = float(page.rect.width)
            h_pt = float(page.rect.height)
            if target_height_px and target_height_px > 0:
                scale = max(0.1, float(target_height_px) / h_pt)
                mat = fitz.Matrix(scale, scale)
            else:
                mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            # 使用 PNG 流插入，保留图像质量
            stream = pix.tobytes("png")
            new_page = out_doc.new_page(width=w_pt, height=h_pt)
            rect = fitz.Rect(0.0, 0.0, w_pt, h_pt)
            new_page.insert_image(rect, stream=stream)
            if progress_cb:
                try:
                    progress_cb((i + 1) * 100.0 / total, f"写入第 {i+1} 页")
                except Exception:
                    pass
    finally:
        try:
            doc.close()
        except Exception:
            pass

    os.makedirs(os.path.dirname(output_pdf_path) or ".", exist_ok=True)
    out_doc.save(output_pdf_path)
    out_doc.close()
    return output_pdf_path


class _ImagePDFWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        pdf_path: str,
        out_path: str,
        zoom: float,
        target_height_px: Optional[int],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.out_path = out_path
        self.zoom = zoom
        self.target_height_px = target_height_px

    def run(self):
        try:
            def cb(pct, msg):
                self.progress.emit(int(pct))
            out = convert_pdf_to_image_only_pdf(
                input_pdf_path=self.pdf_path,
                output_pdf_path=self.out_path,
                zoom=self.zoom,
                target_height_px=self.target_height_px,
                progress_cb=cb,
            )
            self.finished.emit(out)
        except Exception as e:
            self.failed.emit(str(e))


class PdfToImagePDFWindow(QWidget):
    """
    PDF 转纯图 PDF：将每页渲染为图片并写入新 PDF，仅包含图像内容。
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
        title = QLabel("PDF 转纯图PDF")
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
        self.edit_pdf = QLineEdit(); self.edit_pdf.setMinimumHeight(dp(self.scale, 32)); self.edit_pdf.setReadOnly(True)
        lay.addWidget(self.btn_choose_pdf)
        lay.addWidget(self.edit_pdf)

        self.btn_choose_out = QPushButton("选择输出PDF")
        self.btn_choose_out.setMinimumHeight(dp(self.scale, 32))
        self.btn_choose_out.clicked.connect(self._choose_output)
        self.edit_out = QLineEdit(); self.edit_out.setMinimumHeight(dp(self.scale, 32))
        lay.addWidget(self.btn_choose_out)
        lay.addWidget(self.edit_out)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        try:
            form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
            form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        except Exception:
            pass
        self.spin_zoom = QDoubleSpinBox(); self.spin_zoom.setRange(0.5, 5.0); self.spin_zoom.setSingleStep(0.5); self.spin_zoom.setValue(2.0); self.spin_zoom.setSuffix("x")
        self.spin_height = QSpinBox(); self.spin_height.setRange(0, 20000); self.spin_height.setValue(1600); self.spin_height.setSuffix(" px"); self.spin_height.setSpecialValueText("按缩放")
        form.addRow(QLabel("缩放"), self.spin_zoom)
        form.addRow(QLabel("导出高度(px)"), self.spin_height)
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
            root = self.layout()
            root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
            root.setSpacing(dp(self.scale, 8))
            if hasattr(self, 'title_bar') and self.title_bar and self.title_bar.layout():
                tl = self.title_bar.layout()
                tl.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
                tl.setSpacing(dp(self.scale, 6))
            if hasattr(self, 'btn_min') and self.btn_min:
                self.btn_min.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
                self.btn_min.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
            if hasattr(self, 'btn_close') and self.btn_close:
                self.btn_close.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
                self.btn_close.setFixedSize(dp(self.scale, 40), dp(self.scale, 32))
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
            self.edit_out.setText(os.path.join(out_dir, f"{base}_image.pdf"))

    def _choose_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "选择输出PDF", self.edit_out.text() or "output.pdf", "PDF 文件 (*.pdf)")
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
            out = os.path.join(os.path.dirname(pdf) or ".", f"{base}_image.pdf")
            self.edit_out.setText(out)
        self.btn_start.setEnabled(False)
        self.progress.setValue(0)
        self.log.setText("正在转换...")
        zoom = float(self.spin_zoom.value())
        h = int(self.spin_height.value())
        target_h = h if h > 0 else None
        self._worker = _ImagePDFWorker(pdf, out, zoom, target_h)
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