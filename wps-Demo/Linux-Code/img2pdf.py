#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
from typing import Optional, Tuple, List

import fitz  # PyMuPDF
from PIL import Image

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QFileDialog,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QProgressBar,
    QSizePolicy,
    QBoxLayout,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, QSize, Signal, QThread, QTimer, QUrl
from PySide6.QtGui import QPixmap, QImage, QIcon, QDesktopServices

from ui_style_nb import build_style, compute_scale, dp


# 纸张尺寸（PDF 点，1 点 = 1/72 英寸）
PAPER_SIZES_PT = {
    "A3": (842, 1191),
    "A4": (595, 842),
    "A5": (420, 595),
    "Letter": (612, 792),
    "Legal": (612, 1008),
}


def _page_size(name: str, landscape: bool) -> Tuple[float, float]:
    base = PAPER_SIZES_PT.get(name, PAPER_SIZES_PT["A4"])  # 默认 A4
    w, h = base
    return (h, w) if landscape else (w, h)


def split_image_segments(img_path: str, segment_height_px: int) -> List[Image.Image]:
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"文件不存在: {img_path}")
    im = Image.open(img_path)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    width, height = im.size
    seg_h = max(10, int(segment_height_px))
    segments: List[Image.Image] = []
    top = 0
    while top < height:
        bottom = min(top + seg_h, height)
        box = (0, top, width, bottom)
        seg = im.crop(box)
        segments.append(seg)
        top = bottom
    return segments


def pil_to_qpixmap(img: Image.Image) -> QPixmap:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    qimg = QImage.fromData(data)
    return QPixmap.fromImage(qimg)


def compose_pdf_from_segments(
    segments: List[Image.Image],
    output_path: str,
    paper_name: str = "A4",
    landscape: bool = False,
    margin_pt: float = 20.0,
) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = fitz.open()
    pw, ph = _page_size(paper_name, landscape)
    avail_w = max(0.0, pw - margin_pt * 2)
    avail_h = max(0.0, ph - margin_pt * 2)

    # 目标内容区域按纸张比例（宽:高）自动匹配
    page_ratio = pw / float(ph) if ph > 0 else 1.0
    target_h = avail_h
    target_w = target_h * page_ratio
    if target_w > avail_w:
        target_w = avail_w
        target_h = target_w / page_ratio

    for i, seg in enumerate(segments, 1):
        if seg.mode not in ("RGB", "L"):
            seg = seg.convert("RGB")
        seg_w, seg_h = seg.size
        if seg_w <= 0 or seg_h <= 0:
            continue

        # 缩放以适配目标内容区域（不拉伸变形）
        scale_w = target_w / float(seg_w)
        scale_h = target_h / float(seg_h)
        scale = min(scale_w, scale_h) if (scale_w > 0 and scale_h > 0) else 1.0
        draw_w = seg_w * scale
        draw_h = seg_h * scale

        # 横向居中，纵向贴近上边距
        x = (pw - draw_w) / 2.0
        y = margin_pt

        page = doc.new_page(width=pw, height=ph)

        buf = io.BytesIO()
        seg.save(buf, format="PNG")
        stream = buf.getvalue()
        rect = fitz.Rect(x, y, x + draw_w, y + draw_h)
        page.insert_image(rect, stream=stream)

    doc.save(output_path)
    doc.close()
    return output_path


class _GenerateWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        img_path: str,
        segment_height_px: int,
        output_path: str,
        paper_name: str,
        landscape: bool,
        margin_pt: int,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.img_path = img_path
        self.segment_height_px = segment_height_px
        self.output_path = output_path
        self.paper_name = paper_name
        self.landscape = landscape
        self.margin_pt = margin_pt

    def run(self):
        try:
            segments = split_image_segments(self.img_path, self.segment_height_px)
            total = len(segments)
            if total == 0:
                raise RuntimeError("无法生成分段，请检查裁剪高度与图片有效性")

            doc = fitz.open()
            pw, ph = _page_size(self.paper_name, self.landscape)
            avail_w = max(0.0, pw - self.margin_pt * 2)
            avail_h = max(0.0, ph - self.margin_pt * 2)

            # 目标内容区域按纸张比例（宽:高）自动匹配
            page_ratio = pw / float(ph) if ph > 0 else 1.0
            target_h = avail_h
            target_w = target_h * page_ratio
            if target_w > avail_w:
                target_w = avail_w
                target_h = target_w / page_ratio

            for i, seg in enumerate(segments, 1):
                if seg.mode not in ("RGB", "L"):
                    seg = seg.convert("RGB")
                seg_w, seg_h = seg.size
                if seg_w <= 0 or seg_h <= 0:
                    continue

                scale_w = target_w / float(seg_w)
                scale_h = target_h / float(seg_h)
                scale = min(scale_w, scale_h) if (scale_w > 0 and scale_h > 0) else 1.0
                draw_w = seg_w * scale
                draw_h = seg_h * scale

                x = (pw - draw_w) / 2.0
                y = self.margin_pt
                page = doc.new_page(width=pw, height=ph)

                buf = io.BytesIO()
                seg.save(buf, format="PNG")
                stream = buf.getvalue()
                rect = fitz.Rect(x, y, x + draw_w, y + draw_h)
                page.insert_image(rect, stream=stream)

                self.progress.emit(int(i * 100 / total))

            os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)
            doc.save(self.output_path)
            doc.close()
            self.finished.emit(self.output_path)
        except Exception as e:
            self.failed.emit(str(e))


class _GenerateImagesWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        image_paths: List[str],
        output_path: str,
        paper_name: str,
        landscape: bool,
        margin_pt: int,
        segment_height_px: int,
        do_split: bool,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.image_paths = image_paths
        self.output_path = output_path
        self.paper_name = paper_name
        self.landscape = landscape
        self.margin_pt = margin_pt
        self.segment_height_px = segment_height_px
        self.do_split = do_split

    def run(self):
        try:
            ordered = [p for p in self.image_paths if os.path.exists(p)]
            if len(ordered) == 0:
                raise RuntimeError("未选择图片")

            doc = fitz.open()
            pw, ph = _page_size(self.paper_name, self.landscape)
            avail_w = max(0.0, pw - self.margin_pt * 2)
            avail_h = max(0.0, ph - self.margin_pt * 2)
            page_ratio = pw / float(ph) if ph > 0 else 1.0
            target_h = avail_h
            target_w = target_h * page_ratio
            if target_w > avail_w:
                target_w = avail_w
                target_h = target_w / page_ratio

            if self.do_split:
                all_segments = []
                for p in ordered:
                    segs = split_image_segments(p, self.segment_height_px)
                    for s in segs:
                        all_segments.append((p, s))
                total_pages = len(all_segments)
                if total_pages == 0:
                    raise RuntimeError("无法生成分段")
                for i, (_, seg) in enumerate(all_segments, 1):
                    if seg.mode not in ("RGB", "L"):
                        seg = seg.convert("RGB")
                    iw, ih = seg.size
                    if iw <= 0 or ih <= 0:
                        continue
                    scale_w = target_w / float(iw)
                    scale_h = target_h / float(ih)
                    scale = min(scale_w, scale_h) if (scale_w > 0 and scale_h > 0) else 1.0
                    draw_w = iw * scale
                    draw_h = ih * scale
                    x = (pw - draw_w) / 2.0
                    y = self.margin_pt
                    page = doc.new_page(width=pw, height=ph)
                    buf = io.BytesIO()
                    seg.save(buf, format="PNG")
                    stream = buf.getvalue()
                    rect = fitz.Rect(x, y, x + draw_w, y + draw_h)
                    page.insert_image(rect, stream=stream)
                    self.progress.emit(int(i * 100 / total_pages))
            else:
                total = len(ordered)
                for i, p in enumerate(ordered, 1):
                    im = Image.open(p)
                    if im.mode not in ("RGB", "L"):
                        im = im.convert("RGB")
                    iw, ih = im.size
                    if iw <= 0 or ih <= 0:
                        continue
                    scale_w = target_w / float(iw)
                    scale_h = target_h / float(ih)
                    scale = min(scale_w, scale_h) if (scale_w > 0 and scale_h > 0) else 1.0
                    draw_w = iw * scale
                    draw_h = ih * scale
                    x = (pw - draw_w) / 2.0
                    y = self.margin_pt
                    page = doc.new_page(width=pw, height=ph)
                    buf = io.BytesIO()
                    im.save(buf, format="PNG")
                    stream = buf.getvalue()
                    rect = fitz.Rect(x, y, x + draw_w, y + draw_h)
                    page.insert_image(rect, stream=stream)
                    self.progress.emit(int(i * 100 / total))

            os.makedirs(os.path.dirname(self.output_path) or ".", exist_ok=True)
            doc.save(self.output_path)
            doc.close()
            self.finished.emit(self.output_path)
        except Exception as e:
            self.failed.emit(str(e))


class Img2PDFWindow(QWidget):
    """
    图片转 PDF（长图裁剪 + 预览 + 纸张自适应）

    - 上传图片，设置裁剪高度（像素）
    - 预览分割后的每页效果与尺寸
    - 支持预设纸张尺寸（A4、A3、A5、Letter、Legal），自动缩放匹配
    - 可选横向（landscape），边距可调（点）
    """

    def __init__(self, scale: Optional[float] = None, embedded: bool = False):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())
        self.embedded = embedded
        self.setMinimumSize(dp(self.scale, 840), dp(self.scale, 520))

        # 状态
        self.image_path: Optional[str] = None
        self.image_paths: List[str] = []
        self.segments: List[Image.Image] = []
        self.current_index: int = 0
        self.mode: str = "single_long"

        self.setStyleSheet(build_style(self.scale))
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
        root.setSpacing(dp(self.scale, 8))

        # 顶部标题与控制按钮
        self.title_bar_layout = QHBoxLayout()
        title = QLabel("图片转PDF")
        self.title_bar_layout.addWidget(title)
        self.title_bar_layout.addStretch(1)
        btn_min = QPushButton("最小化")
        btn_close = QPushButton("关闭")
        btn_min.clicked.connect(self._do_minimize)
        btn_close.clicked.connect(self._do_close)
        self.title_bar_layout.addWidget(btn_min)
        self.title_bar_layout.addWidget(btn_close)
        root.addLayout(self.title_bar_layout)

        # 主体：左侧预览 + 右侧控制（改为可拖拽的分割布局）
        self.main_splitter = QSplitter(Qt.Horizontal)
        try:
            self.main_splitter.setHandleWidth(dp(self.scale, 6))
        except Exception:
            pass

        # 左侧预览
        preview_card = QFrame()
        preview_card.setObjectName("PanelCard")
        preview_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        pv_layout = QVBoxLayout(preview_card)
        pv_layout.setContentsMargins(dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8))
        pv_layout.setSpacing(dp(self.scale, 6))

        self.preview_area = QScrollArea()
        self.preview_area.setFrameShape(QFrame.NoFrame)
        self.preview_area.setWidgetResizable(True)
        try:
            # 让滚动条与预览内容之间留出一点缝隙
            self.preview_area.setViewportMargins(0, 0, dp(self.scale, 6), 0)
        except Exception:
            pass
        self.preview_label = QLabel("上传图片以预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setMinimumSize(dp(self.scale, 360), dp(self.scale, 240))
        self.preview_area.setWidget(self.preview_label)
        pv_layout.addWidget(self.preview_area, 1)

        self.nav_row = QHBoxLayout()
        self.btn_prev = QPushButton("上一页"); self.btn_prev.setMinimumHeight(dp(self.scale, 32))
        self.btn_next = QPushButton("下一页"); self.btn_next.setMinimumHeight(dp(self.scale, 32))
        self.btn_prev.clicked.connect(self._prev)
        self.btn_next.clicked.connect(self._next)
        self.page_info = QLabel("第 0/0 页"); self.page_info.setMinimumHeight(dp(self.scale, 24))
        self.nav_row.addWidget(self.btn_prev)
        self.nav_row.addWidget(self.btn_next)
        self.nav_row.addStretch(1)
        self.nav_row.addWidget(self.page_info)
        pv_layout.addLayout(self.nav_row)

        self.main_splitter.addWidget(preview_card)

        # 右侧控制
        self.ctrl_card = QFrame()
        self.ctrl_card.setObjectName("PanelCard")
        # 右侧控制卡片横纵都跟随容器扩展，类似 streamlit 的“充满宽度”效果
        self.ctrl_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ctrl = QVBoxLayout(self.ctrl_card)
        ctrl.setContentsMargins(dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8))
        ctrl.setSpacing(dp(self.scale, 6))

        # 上传与输出
        self.row_up = QHBoxLayout()
        self.btn_choose = QPushButton("选择图片"); self.btn_choose.setMinimumHeight(dp(self.scale, 32))
        self.btn_add_images = QPushButton("追加图片"); self.btn_add_images.setMinimumHeight(dp(self.scale, 32))
        try:
            self.btn_add_images.setToolTip("批量追加图片到列表（不替换现有）")
        except Exception:
            pass
        self.path_edit = QLineEdit(); self.path_edit.setMinimumHeight(dp(self.scale, 32)); self.path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.path_edit.setPlaceholderText("请选择要转换的图片文件（PNG/JPEG/BMP 等）")
        self.btn_choose.clicked.connect(self._choose_image)
        self.btn_add_images.clicked.connect(self._choose_images)
        self.row_up.addWidget(self.btn_choose)
        self.row_up.addWidget(self.btn_add_images)
        self.row_up.addWidget(self.path_edit, 1)
        ctrl.addLayout(self.row_up)

        self.row_out = QHBoxLayout()
        self.btn_out = QPushButton("输出PDF"); self.btn_out.setMinimumHeight(dp(self.scale, 32))
        self.out_edit = QLineEdit(); self.out_edit.setMinimumHeight(dp(self.scale, 32)); self.out_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.out_edit.setPlaceholderText("输出PDF路径（默认与图片同目录）")
        self.btn_out.clicked.connect(self._choose_output)
        self.row_out.addWidget(self.btn_out)
        self.row_out.addWidget(self.out_edit, 1)
        ctrl.addLayout(self.row_out)

        # 模式与裁剪、纸张设置
        self.row_mode = QHBoxLayout()
        lab_mode = QLabel("源类型")
        self.combo_mode = QComboBox(); self.combo_mode.setMinimumHeight(dp(self.scale, 32))
        self.combo_mode.addItem("长图裁剪")
        self.combo_mode.addItem("批量裁剪拼接")
        self.combo_mode.currentTextChanged.connect(self._on_mode_changed)
        self.row_mode.addWidget(lab_mode)
        self.row_mode.addWidget(self.combo_mode)
        ctrl.addLayout(self.row_mode)
        self.row_crop = QHBoxLayout()
        lab_h = QLabel("裁剪高度(px)")
        self.spin_h = QSpinBox(); self.spin_h.setMinimumHeight(dp(self.scale, 32))
        self.spin_h.setRange(50, 50000)
        self.spin_h.setValue(800)
        self.spin_h.valueChanged.connect(self._refresh_segments)
        self.chk_batch_split = QCheckBox("按裁剪高度分页"); self.chk_batch_split.setMinimumHeight(dp(self.scale, 28))
        self.chk_batch_split.setChecked(True)
        self.row_crop.addWidget(lab_h)
        self.row_crop.addWidget(self.spin_h)
        self.row_crop.addWidget(self.chk_batch_split)
        ctrl.addLayout(self.row_crop)

        self.row_paper = QHBoxLayout()
        lab_paper = QLabel("纸张尺寸")
        self.combo_paper = QComboBox(); self.combo_paper.setMinimumHeight(dp(self.scale, 32))
        for name in ("A4", "A3", "A5", "Letter", "Legal"):
            self.combo_paper.addItem(name)
        self.combo_paper.setCurrentText("A4")
        self.combo_paper.currentTextChanged.connect(self._update_preview)
        self.chk_land = QCheckBox("横向"); self.chk_land.setMinimumHeight(dp(self.scale, 28))
        self.chk_land.stateChanged.connect(self._update_preview)
        self.row_paper.addWidget(lab_paper)
        self.row_paper.addWidget(self.combo_paper)
        self.row_paper.addWidget(self.chk_land)
        ctrl.addLayout(self.row_paper)

        self.row_margin = QHBoxLayout()
        lab_margin = QLabel("边距(pt)")
        self.spin_margin = QSpinBox(); self.spin_margin.setMinimumHeight(dp(self.scale, 32))
        self.spin_margin.setRange(0, 100)
        self.spin_margin.setValue(20)
        self.spin_margin.valueChanged.connect(self._update_preview)
        self.row_margin.addWidget(lab_margin)
        self.row_margin.addWidget(self.spin_margin)
        ctrl.addLayout(self.row_margin)

        # 页预览列表（可点选跳转）
        lab_pages = QLabel("页预览")
        ctrl.addWidget(lab_pages)
        self.list_pages = QListWidget(); self.list_pages.setMinimumHeight(dp(self.scale, 120)); self.list_pages.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_pages.itemClicked.connect(self._on_page_clicked)
        ctrl.addWidget(self.list_pages)

        lab_images = QLabel("图片列表")
        ctrl.addWidget(lab_images)
        self.list_images = QListWidget(); self.list_images.setMinimumHeight(dp(self.scale, 120)); self.list_images.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_images.setDragDropMode(QAbstractItemView.InternalMove)
        try:
            self.list_images.setDragEnabled(True)
            self.list_images.setAcceptDrops(True)
            self.list_images.setDropIndicatorShown(True)
            self.list_images.setSelectionMode(QAbstractItemView.ExtendedSelection)
        except Exception:
            pass
        self.list_images.itemClicked.connect(self._on_image_clicked)
        ctrl.addWidget(self.list_images)

        self.images_ops_widget = QFrame()
        self.row_images_ops = QHBoxLayout(self.images_ops_widget)
        self.btn_remove_selected = QPushButton("删除选中"); self.btn_remove_selected.setMinimumHeight(dp(self.scale, 32))
        self.btn_clear_list = QPushButton("清空列表"); self.btn_clear_list.setMinimumHeight(dp(self.scale, 32))
        self.btn_remove_selected.clicked.connect(self._remove_selected_images)
        self.btn_clear_list.clicked.connect(self._clear_image_list)
        self.row_images_ops.addWidget(self.btn_remove_selected)
        self.row_images_ops.addWidget(self.btn_clear_list)
        ctrl.addWidget(self.images_ops_widget)

        # 操作按钮与进度
        self.row_ops = QHBoxLayout()
        self.btn_gen = QPushButton("开始生成PDF"); self.btn_gen.setMinimumHeight(dp(self.scale, 32))
        self.btn_gen.clicked.connect(self._start_generate)
        self.row_ops.addWidget(self.btn_gen)
        self.row_ops.addStretch(1)
        self.progress = QProgressBar(); self.progress.setMinimumHeight(dp(self.scale, 24))
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.row_ops.addWidget(self.progress)
        ctrl.addLayout(self.row_ops)

        self.log_label = QLabel(""); self.log_label.setWordWrap(True); self.log_label.setMinimumHeight(dp(self.scale, 24))
        ctrl.addWidget(self.log_label)

        self.main_splitter.addWidget(self.ctrl_card)
        try:
            self.main_splitter.setCollapsible(0, False)
            self.main_splitter.setCollapsible(1, False)
            self.main_splitter.setStretchFactor(0, 3)
            self.main_splitter.setStretchFactor(1, 2)
        except Exception:
            pass
        root.addWidget(self.main_splitter, 1)
        # 初始进行一次自适应重排
        QTimer.singleShot(0, self._reflow_layout)
        QTimer.singleShot(0, self._apply_responsive_sizes)
        # 每秒自动检测并重排
        self._auto_timer = QTimer(self)
        self._auto_timer.setInterval(1000)
        self._auto_timer.timeout.connect(self._reflow_layout)
        self._auto_timer.start()
        try:
            self.chk_batch_split.stateChanged.connect(self._update_generate_button_text)
        except Exception:
            pass
        self._on_mode_changed(self.combo_mode.currentText())

    def _sum_layout_min_width(self, lay: QBoxLayout) -> int:
        try:
            total = 0
            count = lay.count()
            for i in range(count):
                it = lay.itemAt(i)
                w = it.widget()
                l = it.layout()
                s = it.spacerItem()
                if w is not None:
                    total += w.minimumSizeHint().width()
                elif l is not None:
                    total += l.minimumSize().width()
                elif s is not None:
                    total += s.sizeHint().width()
            total += max(0, count - 1) * lay.spacing()
            m = lay.contentsMargins()
            total += (m.left() + m.right())
            return max(1, total)
        except Exception:
            return 1

    def _sum_layout_min_height(self, lay: QBoxLayout) -> int:
        try:
            total = 0
            count = lay.count()
            for i in range(count):
                it = lay.itemAt(i)
                w = it.widget()
                l = it.layout()
                s = it.spacerItem()
                if w is not None:
                    total += w.minimumSizeHint().height()
                elif l is not None:
                    total += l.minimumSize().height()
                elif s is not None:
                    total += s.sizeHint().height()
            total += max(0, count - 1) * lay.spacing()
            m = lay.contentsMargins()
            total += (m.top() + m.bottom())
            return max(1, total)
        except Exception:
            return 1

    def _reflow_layout(self):
        # 根据可用宽度：
        # 1) 右侧面板各行在拥挤时纵向堆叠；
        # 2) 左右两卡片在拥挤时改为上下纵向（通过 QSplitter 切换方向）。
        try:
            avail_w = self.ctrl_card.width() - dp(self.scale, 32)
            if avail_w <= 0:
                # 尚未布局完成，使用窗口宽度的三分之一作为估计
                avail_w = max(1, self.width() // 3)

            rows = [
                self.row_up,
                self.row_out,
                self.row_mode,
                self.row_crop,
                self.row_paper,
                self.row_margin,
                self.row_images_ops,
                self.row_ops,
                self.nav_row,
            ]
            for row in rows:
                need_w = self._sum_layout_min_width(row)
                row.setDirection(QBoxLayout.LeftToRight if need_w <= avail_w else QBoxLayout.TopToBottom)

            # 左右卡片是否需要上下堆叠
            try:
                # 估算左右并排需要的最小宽度
                need_center_w = (
                    self.preview_label.sizeHint().width()
                    + self.ctrl_card.sizeHint().width()
                    + dp(self.scale, 8)
                )
                root_m = self.layout().contentsMargins()
                avail_total_w = max(1, self.width() - (root_m.left() + root_m.right()))
                self.main_splitter.setOrientation(
                    Qt.Horizontal if need_center_w <= avail_total_w else Qt.Vertical
                )
            except Exception:
                pass
        except Exception:
            pass

    def _calc_size_factor(self) -> float:
        try:
            # 宽度因子：随右侧面板可用宽度变化
            base_w = max(1, dp(self.scale, 420))
            panel_w = max(1, self.ctrl_card.width())
            factor_w = panel_w / float(base_w)

            # 高度因子：按右侧面板可用高度与内容最小需求比值自动压缩
            lay = self.ctrl_card.layout()
            need_h = self._sum_layout_min_height(lay) if lay is not None else dp(self.scale, 640)
            avail_h = max(1, self.ctrl_card.height())
            ratio_h = min(1.0, avail_h / float(max(1, need_h)))

            # 综合（宽度权重 0.6，高度权重 0.4），允许更强的压缩下限
            f = (factor_w * 0.6 + ratio_h * 0.4)
            return max(0.50, min(1.15, f))
        except Exception:
            return 1.0

    def _apply_responsive_sizes(self):
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

            # 右侧控件
            ensure_h(self.btn_choose, 32)
            ensure_h(self.btn_add_images, 32)
            ensure_h(self.path_edit, 32)
            ensure_h(self.btn_out, 32)
            ensure_h(self.out_edit, 32)
            ensure_h(self.spin_h, 32)
            ensure_h(self.chk_batch_split, 28, extra=6)
            ensure_h(self.combo_paper, 32)
            ensure_h(self.chk_land, 28, extra=6)
            ensure_h(self.spin_margin, 32)
            ensure_h(self.btn_gen, 32)
            ensure_h(self.progress, 24, extra=6)
            ensure_h(self.combo_mode, 32)
            self.list_pages.setMinimumHeight(H(120))
            self.list_images.setMinimumHeight(H(120))
            ensure_h(self.log_label, 24, extra=4)
            ensure_h(self.btn_remove_selected, 32)
            ensure_h(self.btn_clear_list, 32)

            # 预览导航与预览区域最小尺寸
            ensure_h(self.btn_prev, 32)
            ensure_h(self.btn_next, 32)
            a4w, a4h = dp(self.scale, 360), dp(self.scale, 240)
            self.preview_label.setMinimumSize(int(a4w * f), int(a4h * f))
        except Exception:
            pass

    # --- UI 交互 ---
    def _do_minimize(self):
        top = self if self.isWindow() else self.window()
        try:
            top.showMinimized()
        except Exception:
            pass

    def _do_close(self):
        top = self if self.isWindow() else self.window()
        try:
            top.close()
        except Exception:
            pass

    def _choose_image(self):
        if self.mode == "multi_images":
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                "添加图片",
                "",
                "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)",
            )
            if paths:
                self._add_image_paths(paths)
                self.combo_mode.setCurrentText("多图合并")
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "选择图片",
                "",
                "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)",
            )
            if path:
                self.image_path = path
                self.path_edit.setText(path)
                base = os.path.splitext(os.path.basename(path))[0]
                out_dir = os.path.dirname(path) or "."
                self.out_edit.setText(os.path.join(out_dir, f"{base}_converted.pdf"))
                self._refresh_segments()

    def _choose_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "添加图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)",
        )
        if paths:
            self._add_image_paths(paths)
            self.combo_mode.setCurrentText("多图合并")

    def _add_image_paths(self, paths: List[str]):
        prev_len = len(self.image_paths)
        self.mode = "multi_images"
        for p in paths:
            self.image_paths.append(p)
            try:
                im = Image.open(p)
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                pm = pil_to_qpixmap(im)
            except Exception:
                pm = QPixmap()
            if not pm.isNull():
                pm = pm.scaledToHeight(dp(self.scale, 80), Qt.SmoothTransformation)
            item = QListWidgetItem()
            item.setText(os.path.basename(p))
            item.setData(Qt.UserRole, p)
            if not pm.isNull():
                item.setIcon(QIcon(pm))
            self.list_images.addItem(item)
        if len(self.image_paths) > 0 and prev_len == 0:
            self.current_index = 0
        self._update_preview()

    def _choose_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "选择输出PDF", self.out_edit.text() or "output.pdf", "PDF 文件 (*.pdf)"
        )
        if path:
            self.out_edit.setText(path)

    def _refresh_segments(self):
        self.segments = []
        self.current_index = 0
        self.list_pages.clear()
        if not self.image_path:
            self.preview_label.setText("上传图片以预览")
            self.preview_label.setPixmap(QPixmap())
            self.page_info.setText("第 0/0 页")
            return
        try:
            seg_h = int(self.spin_h.value())
            self.segments = split_image_segments(self.image_path, seg_h)
            for i, seg in enumerate(self.segments, 1):
                pm = pil_to_qpixmap(seg)
                if not pm.isNull():
                    pm = pm.scaledToHeight(dp(self.scale, 80), Qt.SmoothTransformation)
                item = QListWidgetItem()
                item.setText(f"第 {i} 页")
                item.setData(Qt.UserRole, i - 1)
                if not pm.isNull():
                    item.setIcon(QIcon(pm))
                self.list_pages.addItem(item)
            self._update_preview()
        except Exception as e:
            self.log_label.setText(f"分段失败：{e}")

    def _on_page_clicked(self, item: QListWidgetItem):
        try:
            idx = int(item.data(Qt.UserRole))
            self.current_index = max(0, min(idx, len(self.segments) - 1))
            self._update_preview()
        except Exception:
            pass

    def _on_image_clicked(self, item: QListWidgetItem):
        try:
            path = str(item.data(Qt.UserRole))
            idx = self.image_paths.index(path) if path in self.image_paths else 0
            self.current_index = max(0, min(idx, len(self.image_paths) - 1))
            self._update_preview()
        except Exception:
            pass

    def _prev(self):
        if self.mode == "multi_images":
            if not self.image_paths:
                return
            if self.current_index > 0:
                self.current_index -= 1
                self._update_preview()
        else:
            if not self.segments:
                return
            if self.current_index > 0:
                self.current_index -= 1
                self._update_preview()

    def _next(self):
        if self.mode == "multi_images":
            if not self.image_paths:
                return
            if self.current_index + 1 < len(self.image_paths):
                self.current_index += 1
                self._update_preview()
        else:
            if not self.segments:
                return
            if self.current_index + 1 < len(self.segments):
                self.current_index += 1
                self._update_preview()

    def _update_preview(self):
        if self.mode == "multi_images":
            if not self.image_paths:
                self.preview_label.setPixmap(QPixmap())
                self.preview_label.setText("添加图片以预览")
                self.page_info.setText("第 0/0 页")
                return
            try:
                im = Image.open(self.image_paths[self.current_index])
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                pm = pil_to_qpixmap(im)
            except Exception:
                pm = QPixmap()
        else:
            if not self.segments:
                self.preview_label.setPixmap(QPixmap())
                self.preview_label.setText("上传图片以预览")
                self.page_info.setText("第 0/0 页")
                return
            seg = self.segments[self.current_index]
            pm = pil_to_qpixmap(seg)
        # 模拟页面尺寸的适配显示：按选中纸张与横向设置，计算比例，再适配到预览窗口
        paper = self.combo_paper.currentText() or "A4"
        landscape = self.chk_land.isChecked()
        margin = int(self.spin_margin.value())
        pw, ph = _page_size(paper, landscape)
        # 将 PDF 点单位转换为“显示像素”的比例：简单按 1 点≈1.33px（96dpi）
        # 仅用于预览大小感知，不影响实际 PDF 输出
        px_per_pt = 96.0 / 72.0
        vw_base = int(pw * px_per_pt) - int(margin * 2 * px_per_pt)
        vh_base = int(ph * px_per_pt) - int(margin * 2 * px_per_pt)
        vw_base = max(1, vw_base)
        vh_base = max(1, vh_base)
        # 按容器（视口）限制，避免溢出窗口边界
        vp_size = self.preview_area.viewport().size()
        target_w = max(1, min(vw_base, vp_size.width() - dp(self.scale, 8)))
        target_h = max(1, min(vh_base, vp_size.height() - dp(self.scale, 8)))
        pm = pm.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_label.setPixmap(pm)
        self.preview_label.setAlignment(Qt.AlignCenter)
        total = len(self.image_paths) if self.mode == "multi_images" else len(self.segments)
        self.page_info.setText(f"第 {self.current_index+1}/{total} 页  · {paper}{'-横向' if landscape else ''}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 窗口变化时刷新预览，以保持在可视容器内的自适配
        try:
            self._update_preview()
            # 同步执行自适应重排，避免横向拥挤
            self._reflow_layout()
            # 根据 scale 与窗口尺寸自动调整控件高度
            self._apply_responsive_sizes()
        except Exception:
            pass

    def _on_mode_changed(self, text: str):
        self.mode = "multi_images" if (text or "") != "长图裁剪" else "single_long"
        is_multi = self.mode == "multi_images"
        self.btn_choose.setVisible(True)
        self.path_edit.setVisible(not is_multi)
        self.list_pages.setVisible(not is_multi)
        self.btn_add_images.setVisible(True)
        self.list_images.setVisible(is_multi)
        self.images_ops_widget.setVisible(is_multi)
        self._update_generate_button_text()
        self._update_preview()

    def _update_generate_button_text(self):
        try:
            if self.mode == "multi_images" and bool(self.chk_batch_split.isChecked()):
                self.btn_gen.setText("开始批量裁剪并生成PDF")
            else:
                self.btn_gen.setText("开始生成PDF")
        except Exception:
            pass

    def _remove_selected_images(self):
        items = self.list_images.selectedItems()
        if not items:
            return
        for it in items:
            path = str(it.data(Qt.UserRole))
            try:
                idx = self.image_paths.index(path)
                self.image_paths.pop(idx)
            except Exception:
                pass
            row = self.list_images.row(it)
            self.list_images.takeItem(row)
        self.current_index = 0 if self.image_paths else 0
        self._update_preview()

    def _clear_image_list(self):
        self.image_paths = []
        self.list_images.clear()
        self.current_index = 0
        self._update_preview()

    def _start_generate(self):
        paper = self.combo_paper.currentText() or "A4"
        land = self.chk_land.isChecked()
        margin = int(self.spin_margin.value())
        out = self.out_edit.text().strip()
        if self.mode == "multi_images":
            items = [self.list_images.item(i) for i in range(self.list_images.count())]
            ordered_paths = [str(it.data(Qt.UserRole)) for it in items if it and it.data(Qt.UserRole)]
            if not ordered_paths:
                self.log_label.setText("请先添加图片")
                return
            if not out:
                base = os.path.splitext(os.path.basename(ordered_paths[0]))[0]
                out = os.path.join(os.path.dirname(ordered_paths[0]) or ".", f"{base}_merged.pdf")
                self.out_edit.setText(out)
            self.btn_gen.setEnabled(False)
            self.progress.setValue(0)
            self.log_label.setText("正在生成PDF...")
            self._worker = _GenerateImagesWorker(
                image_paths=ordered_paths,
                output_path=out,
                paper_name=paper,
                landscape=land,
                margin_pt=margin,
                segment_height_px=int(self.spin_h.value()),
                do_split=bool(self.chk_batch_split.isChecked()),
            )
            self._worker.progress.connect(self.progress.setValue)
            self._worker.finished.connect(self._on_generate_ok)
            self._worker.failed.connect(self._on_generate_fail)
            self._worker.finished.connect(lambda _: self.btn_gen.setEnabled(True))
            self._worker.failed.connect(lambda _: self.btn_gen.setEnabled(True))
            self._worker.start()
        else:
            if not self.image_path:
                self.log_label.setText("请先选择图片")
                return
            if not self.segments:
                self.log_label.setText("请调整裁剪高度以生成预览")
                return
            if not out:
                base = os.path.splitext(os.path.basename(self.image_path))[0]
                out = os.path.join(os.path.dirname(self.image_path) or ".", f"{base}_converted.pdf")
                self.out_edit.setText(out)
            self.btn_gen.setEnabled(False)
            self.progress.setValue(0)
            self.log_label.setText("正在生成PDF...")
            self._worker = _GenerateWorker(
                img_path=self.image_path,
                segment_height_px=int(self.spin_h.value()),
                output_path=out,
                paper_name=paper,
                landscape=land,
                margin_pt=margin,
            )
            self._worker.progress.connect(self.progress.setValue)
            self._worker.finished.connect(self._on_generate_ok)
            self._worker.failed.connect(self._on_generate_fail)
            self._worker.finished.connect(lambda _: self.btn_gen.setEnabled(True))
            self._worker.failed.connect(lambda _: self.btn_gen.setEnabled(True))
            self._worker.start()

    def _on_generate_ok(self, path: str):
        self.log_label.setText(f"生成完成：{path}")
        try:
            if os.path.exists(path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))
        except Exception:
            pass

    def _on_generate_fail(self, msg: str):
        self.log_label.setText(f"生成失败：{msg}")


def launch_app():
    app = QApplication([])
    app.setApplicationName("图片转PDF")
    win = Img2PDFWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    launch_app()