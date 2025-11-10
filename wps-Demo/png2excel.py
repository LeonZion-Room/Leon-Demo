#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import threading
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

try:
    import cv2
except Exception:
    cv2 = None  # Lazy import guard; UI 会提示安装依赖

try:
    import easyocr  # 作为首选 OCR
except Exception:
    easyocr = None

try:
    import pytesseract  # 作为备用 OCR（需要系统安装 Tesseract-OCR）
except Exception:
    pytesseract = None

try:
    from rapidocr_onnxruntime import RapidOCR  # 更轻量的离线 OCR（ONNXRuntime，CPU）
except Exception:
    RapidOCR = None

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QFileDialog,
    QLineEdit,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage

from ui_style_nb import build_style, compute_scale, dp

def _dbg(msg: str) -> None:
    try:
        print(f"[PNG2Excel] {msg}", flush=True)
    except Exception:
        pass


def _ensure_models_dir() -> None:
    try:
        frozen = getattr(sys, "frozen", False)
        base = os.path.dirname(sys.executable) if frozen else os.getcwd()
        dst = os.path.join(base, "rapidocr_models")
        if os.path.isdir(dst):
            return
        src = None
        # 优先从内嵌资源（_MEIPASS）复制
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            cand = os.path.join(meipass, "rapidocr_models")
            if os.path.isdir(cand):
                src = cand
        # 开发模式的备用源
        if src is None:
            dev_src = os.path.join(base, "rapidocr_models")
            if os.path.isdir(dev_src):
                src = dev_src
        if src and os.path.isdir(src):
            import shutil
            shutil.copytree(src, dst, dirs_exist_ok=True)
            _dbg(f"已从资源复制 rapidocr_models 到：{dst}")
    except Exception as e:
        _dbg(f"自动创建 rapidocr_models 失败：{e}")

def _resource_path(rel: str) -> str:
    """仅在 exe 同目录解析资源路径（用户要求）。
    - 冻结环境：使用 `os.path.dirname(sys.executable)`
    - 非冻结环境：使用当前工作目录（便于开发调试）
    """
    try:
        base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        return os.path.join(base, rel)
    except Exception:
        return rel


def _ensure_tesseract_cmd() -> None:
    """为 Windows 可执行环境自动定位 tesseract.exe（备用方案）。"""
    if pytesseract is None:
        return
    try:
        if getattr(pytesseract.pytesseract, "tesseract_cmd", None):
            if os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                return
    except Exception:
        pass
    candidates: list[str] = []
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd:
        candidates.append(env_cmd)
    candidates.append(_resource_path(os.path.join("Tesseract-OCR", "tesseract.exe")))
    candidates.append(_resource_path(os.path.join("easyocr_models", "Tesseract-OCR", "tesseract.exe")))
    candidates.append(r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
    candidates.append(r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe")
    for cmd in candidates:
        try:
            if cmd and os.path.exists(cmd):
                pytesseract.pytesseract.tesseract_cmd = cmd
                return
        except Exception:
            pass


# RapidOCR 管理（只初始化一次，避免 exe 启动时下载模型）
_rapid_engine: Optional[object] = None
_easyocr_reader: Optional["easyocr.Reader"] = None
_easyocr_lock = threading.Lock()

def _get_rapid_engine() -> Optional[object]:
    global _rapid_engine
    if RapidOCR is None:
        _dbg("RapidOCR 未安装，跳过本地 ONNX 引擎")
        return None
    if _rapid_engine is not None:
        return _rapid_engine
    # 确保运行时存在 rapidocr_models 目录（优先从内嵌资源复制）
    _ensure_models_dir()
    model_root = _resource_path("rapidocr_models")
    if not os.path.isdir(model_root):
        _dbg(f"未找到 rapidocr_models 目录：{model_root}")
        return None
    _dbg(f"RapidOCR 模型目录：{model_root}")
    # 首选用户指定的相对路径模型：rec = rapidocr_models/ch_PP-OCRv3_rec_infer.onnx
    prefer_rec = os.path.join(model_root, "ch_PP-OCRv3_rec_infer.onnx")
    det = rec = cls = None
    if os.path.exists(prefer_rec):
        rec = prefer_rec
        _dbg(f"检测到默认识别模型(rec)：{rec}")
    # 兼容不同版本的构造参数：补齐其余模型
    try:
        for f in os.listdir(model_root):
            p = os.path.join(model_root, f)
            name = f.lower()
            if not name.endswith('.onnx'):
                continue
            if 'det' in name and det is None:
                det = p
            elif 'rec' in name and rec is None:
                rec = p
            elif 'cls' in name and cls is None:
                cls = p
        _dbg(f"模型选择：det={det or 'None'}, rec={rec or 'None'}, cls={cls or 'None'}")
    except Exception as e:
        _dbg(f"扫描 rapidocr_models 失败：{e}")
    # 优先尝试新版本构造
    # 构造参数仅传递已有的模型，避免 None 触发异常
    kwargs = {}
    if det:
        kwargs["det_model_path"] = det
    if rec:
        kwargs["rec_model_path"] = rec
    if cls:
        kwargs["cls_model_path"] = cls

    # 缺失模型的提示（特别是缺 det 时）
    if rec and not det:
        _dbg("RapidOCR 提示：缺少检测模型 det，建议添加 ch_PP-OCRv3_det_infer.onnx 到 rapidocr_models 目录")
    if not rec:
        _dbg("RapidOCR 提示：缺少识别模型 rec，建议添加 ch_PP-OCRv3_rec_infer.onnx 到 rapidocr_models 目录")

    # 先尝试按已知模型显式构造
    try:
        if kwargs:
            _rapid_engine = RapidOCR(**kwargs)
            return _rapid_engine
    except Exception as e:
        _dbg(f"RapidOCR 构造失败：{e}；将尝试目录构造")

    # 再尝试目录构造（需要目录内包含 det/rec/cls 文件）
    try:
        _rapid_engine = RapidOCR(model_path=model_root)
        return _rapid_engine
    except Exception as e:
        _dbg(f"RapidOCR 目录构造失败：{e}")
        _rapid_engine = None
        return None


def _get_easyocr_reader() -> Optional["easyocr.Reader"]:
    """只初始化一次 EasyOCR Reader 并缓存，避免重复加载模型导致卡顿。"""
    global _easyocr_reader
    if easyocr is None:
        return None
    if _easyocr_reader is not None:
        return _easyocr_reader
    with _easyocr_lock:
        if _easyocr_reader is not None:
            return _easyocr_reader
        try:
            model_dir = _resource_path("easyocr_models")
            _easyocr_reader = easyocr.Reader(
                ["ch_sim", "en"],
                gpu=False,
                model_storage_directory=model_dir,
                user_network_directory=model_dir,
                download_enabled=False,
            )
        except Exception:
            _easyocr_reader = None
    return _easyocr_reader

def _ocr_rapidocr(patch: np.ndarray) -> str:
    eng = _get_rapid_engine()
    if eng is None:
        return ""
    try:
        res, _ = eng(patch)
        if not res:
            return ""
        texts = []
        for item in res:
            try:
                # item: [文本, 置信度] 或 [框, 文本, 置信度]
                if isinstance(item, (list, tuple)):
                    if len(item) >= 3:
                        text = item[1]
                    elif len(item) >= 1:
                        text = item[0]
                    else:
                        text = ""
                else:
                    text = str(item)
                if text:
                    texts.append(str(text))
            except Exception:
                pass
        return " ".join(texts).strip()
    except Exception:
        return ""


def _read_image(path: str) -> np.ndarray:
    if cv2 is None:
        raise RuntimeError("未安装 OpenCV (opencv-python)，请先安装依赖")
    img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"无法读取图片: {path}")
    return img


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()
    qimg = QImage.fromData(data)
    return QPixmap.fromImage(qimg)


def _cluster_indices(indices: np.ndarray, gap: int = 3) -> List[int]:
    if indices.size == 0:
        return []
    groups: List[List[int]] = []
    cur: List[int] = [int(indices[0])]
    for v in indices[1:]:
        v = int(v)
        if v - cur[-1] <= gap:
            cur.append(v)
        else:
            groups.append(cur)
            cur = [v]
    groups.append(cur)
    centers = [int(round(float(np.mean(g)))) for g in groups]
    return sorted(centers)


def detect_table_grid(img: np.ndarray) -> Tuple[List[int], List[int]]:
    """基于形态学的简单表格线检测，返回列线 x 坐标与行线 y 坐标。

    要求：表格有清晰的横竖线。对无边框表格效果有限。
    """
    if cv2 is None:
        raise RuntimeError("未安装 OpenCV (opencv-python)，请先安装依赖")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 适应性阈值，反色得到线为白、背景黑
    bin_img = cv2.adaptiveThreshold(
        ~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2
    )

    h = bin_img.copy()
    v = bin_img.copy()
    # 内核尺寸与图像尺寸相关联，宽/高分母越小越容易检测到粗线
    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(1, img.shape[1] // 40), 1))
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(1, img.shape[0] // 40)))
    h = cv2.erode(h, hk)
    h = cv2.dilate(h, hk)
    v = cv2.erode(v, vk)
    v = cv2.dilate(v, vk)

    # 行列投影，聚类得到中心线位置
    proj_x = v.sum(axis=0)  # 垂直线在列方向投影更强
    proj_y = h.sum(axis=1)  # 水平线在行方向投影更强
    # 阈值为最大值的一定比例，避免噪声
    tx = max(10, int(np.max(proj_x) * 0.5))
    ty = max(10, int(np.max(proj_y) * 0.5))
    xs = np.where(proj_x >= tx)[0]
    ys = np.where(proj_y >= ty)[0]
    cols = _cluster_indices(xs, gap=4)
    rows = _cluster_indices(ys, gap=4)

    # 至少需要形成一个网格（>=2 条横线和竖线）
    if len(cols) < 2 or len(rows) < 2:
        raise RuntimeError("未检测到清晰的表格线（请确保图片含有表格边框/线）")
    return cols, rows


def _ocr_easyocr(reader: Optional["easyocr.Reader"], patch: np.ndarray) -> str:
    if reader is None:
        return ""
    # easyocr 接受 RGB
    rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
    try:
        res = reader.readtext(rgb, detail=0)
        return " ".join(res).strip()
    except Exception:
        return ""


def _ocr_tesseract(patch: np.ndarray) -> str:
    if pytesseract is None:
        return ""
    try:
        from PIL import Image as PILImage
        rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
        pil = PILImage.fromarray(rgb)
        # chi_sim 需要系统安装中文训练数据；若不可用则回退英文
        try:
            text = pytesseract.image_to_string(pil, lang="chi_sim+eng")
        except Exception:
            text = pytesseract.image_to_string(pil)
        return text.strip()
    except Exception:
        return ""


def extract_table(img_path: str) -> List[List[str]]:
    """从图片中提取表格并返回二维字符串数组。

    优先使用 EasyOCR；缺失时回退 Tesseract（需系统安装）。
    """
    _dbg(f"开始提取表格：{img_path}")
    img = _read_image(img_path)
    _dbg(f"图片尺寸：{img.shape}")
    cols, rows = detect_table_grid(img)
    _dbg(f"检测到网格：列 {len(cols)} 条，行 {len(rows)} 条")

    # 初始化 OCR 优先级：RapidOCR（本地模型）> EasyOCR（本地模型）> Tesseract
    use_rapid = _get_rapid_engine() is not None
    reader = None
    if not use_rapid:
        reader = _get_easyocr_reader()
    _ensure_tesseract_cmd()  # 作为最终回退方案
    _dbg(f"OCR使用：RapidOCR={'是' if use_rapid else '否'}, EasyOCR={'是' if reader else '否'}, Tesseract={'是' if pytesseract else '否'}")

    table: List[List[str]] = []
    cnt_rapid = cnt_easy = cnt_tess = 0
    t0 = time.time()
    for i in range(len(rows) - 1):
        y1, y2 = rows[i], rows[i + 1]
        row_vals: List[str] = []
        for j in range(len(cols) - 1):
            x1, x2 = cols[j], cols[j + 1]
            # 裁剪单元格并轻微填白边缘，提升 OCR 效果
            pad = 2
            y1p = max(0, y1 + pad)
            y2p = min(img.shape[0], y2 - pad)
            x1p = max(0, x1 + pad)
            x2p = min(img.shape[1], x2 - pad)
            patch = img[y1p:y2p, x1p:x2p]
            text = ""
            if use_rapid:
                text = _ocr_rapidocr(patch)
                if text:
                    cnt_rapid += 1
            if not text and reader is not None:
                text = _ocr_easyocr(reader, patch)
                if text:
                    cnt_easy += 1
            if not text:
                text = _ocr_tesseract(patch)
                if text:
                    cnt_tess += 1
            row_vals.append(text)
        table.append(row_vals)
    _dbg(f"识别完成，用时 {time.time()-t0:.2f}s；Rapid={cnt_rapid}，EasyOCR={cnt_easy}，Tesseract={cnt_tess}")

    return table


def table_to_tsv(table: List[List[str]]) -> str:
    lines = []
    for row in table:
        # 将制表符与换行替换为空格，避免打断粘贴
        clean = [str(c).replace("\t", " ").replace("\n", " ") for c in row]
        lines.append("\t".join(clean))
    return "\n".join(lines)


class _ExtractWorker(QThread):
    finished = Signal(list)  # 2D list
    failed = Signal(str)

    def __init__(self, img_path: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.img_path = img_path

    def run(self):
        try:
            _dbg(f"工作线程开始：{self.img_path}")
            table = extract_table(self.img_path)
            _dbg("工作线程成功：识别完成，返回结果")
            self.finished.emit(table)
        except Exception as e:
            _dbg(f"工作线程失败：{e}")
            self.failed.emit(str(e))


class Png2ExcelWindow(QWidget):
    """图片转Excel（识别表格并复制到剪贴板）"""

    def __init__(self, scale: Optional[float] = None, embedded: bool = False):
        super().__init__()
        self.embedded = embedded
        # 嵌入模式使用 Qt.Widget，避免窗口标志切换导致子控件被销毁
        try:
            self.setWindowFlags(Qt.Widget if embedded else (Qt.FramelessWindowHint | Qt.Window))
        except Exception:
            pass
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())
        self.setStyleSheet(build_style(self.scale))
        self.resize(dp(self.scale, 900), dp(self.scale, 600))

        self.image_path: Optional[str] = None
        self.table: List[List[str]] = []

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
        root.setSpacing(dp(self.scale, 8))

        # 标题栏
        self.title_bar = QFrame(self)
        title_row = QHBoxLayout(self.title_bar)
        title_row.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
        title_row.setSpacing(dp(self.scale, 6))
        title = QLabel("图片转Excel（识别表格并复制到剪贴板）")
        title.setObjectName("Title")
        title_row.addWidget(title)
        title_row.addStretch(1)
        btn_min = QPushButton("最小化")
        btn_close = QPushButton("关闭")
        btn_min.clicked.connect(lambda: (self if self.isWindow() else self.window()).showMinimized())
        btn_close.clicked.connect(lambda: (self if self.isWindow() else self.window()).close())
        title_row.addWidget(btn_min)
        title_row.addWidget(btn_close)
        root.addWidget(self.title_bar)
        if self.embedded:
            self.title_bar.hide()

        # 主体：左预览（原图）+ 右操作与结果
        main_row = QHBoxLayout()
        main_row.setSpacing(dp(self.scale, 8))

        # 左：原图预览
        left = QFrame(self)
        left.setObjectName("PreviewCard")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8))
        left_lay.setSpacing(dp(self.scale, 6))
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setFrameShape(QFrame.NoFrame)
        self.preview_label = QLabel("上传图片以预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(dp(self.scale, 360), dp(self.scale, 240))
        self.preview_area.setWidget(self.preview_label)
        left_lay.addWidget(self.preview_area, 1)
        main_row.addWidget(left, 5)

        # 右：操作与结果
        right = QFrame(self)
        right.setObjectName("PanelCard")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8))
        right_lay.setSpacing(dp(self.scale, 6))

        row_pick = QHBoxLayout()
        self.btn_pick = QPushButton("选择图片")
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择 PNG/JPG/JPEG 等表格图片")
        self.path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_pick.clicked.connect(self._on_pick_image)
        row_pick.addWidget(self.btn_pick)
        row_pick.addWidget(self.path_edit, 1)
        right_lay.addLayout(row_pick)

        self.btn_run = QPushButton("识别并复制到剪贴板")
        self.btn_run.clicked.connect(self._on_run)
        right_lay.addWidget(self.btn_run)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 不确定耗时时显示忙碌条
        self.progress.setVisible(False)
        right_lay.addWidget(self.progress)

        self.tip_label = QLabel("- Made By LZ-Studio")
        self.tip_label.setWordWrap(True)
        right_lay.addWidget(self.tip_label)

        self.table_widget = QTableWidget()
        self.table_widget.setMinimumHeight(dp(self.scale, 200))
        right_lay.addWidget(self.table_widget, 1)

        main_row.addWidget(right, 4)
        root.addLayout(main_row)

        # 响应式调整（简化版）
        QTimer.singleShot(0, self._apply_responsive_sizes)

    def _apply_responsive_sizes(self):
        # 使用 shiboken6 校验控件是否仍然有效，避免已销毁对象引发异常
        try:
            import shiboken6
        except Exception:
            shiboken6 = None

        def ensure_h(w, base: int, extra: int = 8):
            try:
                if w is None:
                    return
                if shiboken6 and hasattr(shiboken6, "isValid") and not shiboken6.isValid(w):
                    return
                fm_h = w.fontMetrics().height() + dp(self.scale, extra)
                w.setMinimumHeight(max(dp(self.scale, base), fm_h))
            except RuntimeError:
                # 内部 C++ 对象可能已删除，安全忽略
                return
            except Exception:
                try:
                    w.setMinimumHeight(dp(self.scale, base))
                except Exception:
                    pass

        ensure_h(getattr(self, "btn_pick", None), 32)
        ensure_h(getattr(self, "path_edit", None), 32)
        ensure_h(getattr(self, "btn_run", None), 36)
        ensure_h(getattr(self, "progress", None), 22, extra=6)

    def _apply_style(self):
        # 供主窗口缩放时调用，统一更新样式与尺寸
        try:
            self.setStyleSheet(build_style(self.scale))
        except Exception:
            pass
        try:
            self._apply_responsive_sizes()
        except Exception:
            pass

    def _on_pick_image(self):
        exts = "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", os.path.join(os.getcwd(), "测试材料"), exts)
        if not path:
            return
        self.image_path = path
        _dbg(f"选择图片：{path}")
        self.path_edit.setText(path)
        try:
            im = Image.open(path)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            self.preview_label.setPixmap(_pil_to_qpixmap(im))
        except Exception:
            self.preview_label.setText("预览失败")

    def _on_run(self):
        if not self.image_path:
            self.tip_label.setText("请先选择图片")
            return
        # 检查依赖
        if cv2 is None:
            self.tip_label.setText("未安装 opencv-python，请安装依赖后重试")
            return
        _dbg("开始识别操作")
        self._set_busy(True)
        self.worker = _ExtractWorker(self.image_path, self)
        self.worker.finished.connect(self._on_ok)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _set_busy(self, busy: bool):
        self.progress.setVisible(busy)
        self.btn_run.setEnabled(not busy)
        self.btn_pick.setEnabled(not busy)

    def _on_ok(self, table: List[List[str]]):
        self._set_busy(False)
        _dbg(f"识别成功：{len(table)} 行 × {max((len(r) for r in table), default=0)} 列")
        self.table = table or []
        # 填充预览表格
        rows = len(self.table)
        cols = max((len(r) for r in self.table), default=0)
        self.table_widget.clear()
        self.table_widget.setRowCount(rows)
        self.table_widget.setColumnCount(cols)
        for i in range(rows):
            for j in range(len(self.table[i])):
                self.table_widget.setItem(i, j, QTableWidgetItem(self.table[i][j]))

        # 复制到剪贴板（TSV）
        tsv = table_to_tsv(self.table)
        QApplication.clipboard().setText(tsv)
        self.tip_label.setText("已复制到剪贴板，直接在 Excel 粘贴即可。")

    def _on_fail(self, msg: str):
        self._set_busy(False)
        _dbg(f"识别失败：{msg}")
        self.tip_label.setText(
            f"识别失败：{msg}\n"
            f"可能原因：未打包 RapidOCR/EasyOCR 本地模型，或系统未安装 Tesseract-OCR。\n"
            f"解决方案：将模型放入 exe 同目录的 rapidocr_models（推荐）或 easyocr_models；若都不可用，请安装 Tesseract-OCR。"
        )


def launch_app():
    # 启动时输出路径与资源基准信息，便于排查打包环境路径问题
    try:
        frozen = getattr(sys, "frozen", False)
        exe_path = sys.executable
        base = os.path.dirname(exe_path) if frozen else os.getcwd()
        _dbg(f"启动应用：cwd={os.getcwd()} frozen={frozen} exe={exe_path}")
        _dbg(f"资源基路径：{base}")
        # 提示默认识别模型存在性
        default_rec = os.path.join(base, "rapidocr_models", "ch_PP-OCRv3_rec_infer.onnx")
        _dbg(f"默认 RapidOCR 识别模型存在：{os.path.exists(default_rec)} -> {default_rec}")
    except Exception:
        pass
    # 运行时自动创建缺失的模型目录（从内嵌资源复制）
    try:
        _ensure_models_dir()
    except Exception:
        pass
    app = QApplication([])
    w = Png2ExcelWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    launch_app()