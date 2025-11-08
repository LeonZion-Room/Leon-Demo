#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LZ-PDF 转 DOCX

一个基于 PyQt5 的简洁 GUI，用于将 PDF 转换为 DOCX。

设计目标：
- 功能与界面分离：可在其他项目中直接调用转换函数。
- 使用已有实现：复用 before/pdf_fc.py 中的 pdf2docx（Word COM）。
- 线程化转换：避免界面卡顿，并显示进度。

运行环境：Windows 10/11 + Microsoft Word + comtypes
"""

import os
import sys
from typing import Callable, Optional

# 将 before 目录加入搜索路径，复用已有功能模块
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BEFORE_DIR = os.path.join(BASE_DIR, "before")
if BEFORE_DIR not in sys.path:
    sys.path.append(BEFORE_DIR)

try:
    # 复用项目中的实现（使用 Word COM 方式）
    from pdf_fc import pdf2docx as core_pdf2docx  # type: ignore
except Exception:
    core_pdf2docx = None  # 延迟在实际调用时提示

from PySide6.QtCore import Qt, QThread, Signal, QPoint, QSize, QCoreApplication
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QFrame,
    QStyle,
    QLineEdit,
    QFormLayout,
    QSizePolicy,
    QInputDialog,
)
from ui_style_nb import build_style, compute_scale, dp, apply_base_font


# -----------------------------
# 功能层（可供其他项目直接调用）
# -----------------------------

def convert_pdf_to_docx(
    pdf_path: str,
    docx_path: Optional[str] = None,
    progress_cb: Optional[Callable[[int, str], None]] = None,
) -> Optional[str]:
    """将 PDF 转换为 DOCX。

    - 复用项目中的 before/pdf_fc.py::pdf2docx 实现（COM + Word）。
    - 提供一个稳定的函数接口，便于其他项目调用。

    Args:
        pdf_path: 输入 PDF 文件路径。
        docx_path: 输出 DOCX 文件路径；为 None 时自动生成同名 .docx。
        progress_cb: 进度回调，形如 progress_cb(percent:int, message:str)。

    Returns:
        生成的 DOCX 文件路径；失败时返回 None。
    """

    if core_pdf2docx is None:
        raise ImportError(
            "未找到 before/pdf_fc.py 或导入失败，请确认项目结构和依赖。"
        )

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {pdf_path}")

    return core_pdf2docx(pdf_path, docx_path, progress_cb)


def suggest_docx_path(pdf_path: str) -> str:
    """根据 PDF 路径生成默认 DOCX 输出路径。"""
    folder = os.path.dirname(pdf_path)
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    return os.path.join(folder, f"{name}.docx")


# -----------------------------
# 工作线程（避免阻塞 UI）
# -----------------------------

class PDF2DOCXWorker(QThread):
    progress = Signal(int, str)
    success = Signal(str)
    failed = Signal(str)

    def __init__(self, pdf_path: str, docx_path: Optional[str] = None):
        super().__init__()
        self.pdf_path = pdf_path
        self.docx_path = docx_path

    def run(self):
        def report(pct: int, msg: str):
            try:
                self.progress.emit(int(pct), str(msg))
            except Exception:
                # 保底：不让异常影响转换主流程
                pass

        try:
            result = convert_pdf_to_docx(self.pdf_path, self.docx_path, report)
            if result and os.path.exists(result):
                self.success.emit(result)
            else:
                self.failed.emit("转换失败：未生成输出文件")
        except Exception as e:
            self.failed.emit(str(e))


# -----------------------------
# 界面层（PyQt5）
# -----------------------------

class PDF2DOCXWindow(QWidget):
    def __init__(self, scale: Optional[float] = None, embedded: bool = False):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowIcon(QIcon())  # 可按需填充图标
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())
        self.embedded = embedded
        self.resize(dp(self.scale, 840), dp(self.scale, 520))
        self._drag_pos: Optional[QPoint] = None

        # 当前选择
        self.pdf_path: Optional[str] = None
        self.docx_path: Optional[str] = None
        self.worker: Optional[PDF2DOCXWorker] = None

        self._build_ui()
        self._apply_style()

    # --- UI 构建 ---
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12))
        root.setSpacing(dp(self.scale, 8))

        # 顶部标题栏（统一样式）
        self.title_bar = QFrame(self)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6), dp(self.scale, 6))
        title_layout.setSpacing(dp(self.scale, 6))
        self.title_label = QLabel("LZ-PDF 转 DOCX")
        self.title_label.setObjectName("Title")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)
        btn_size = QPushButton("窗口大小")
        btn_size.clicked.connect(self.on_set_size)
        btn_full = QPushButton("全屏")
        btn_full.clicked.connect(self.on_toggle_fullscreen)
        title_layout.addWidget(btn_size)
        title_layout.addWidget(btn_full)
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
        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_close)
        root.addWidget(self.title_bar)
        if self.embedded:
            # 嵌入主窗口时隐藏标题栏，统一由主窗口控制
            self.title_bar.hide()
        # 嵌入主窗口时隐藏自身窗口控制按钮，避免与主窗口堆叠
        if not self.isWindow():
            btn_min.hide()
            btn_close.hide()

        # 内容卡片（统一样式）
        panel = QFrame(self)
        panel.setObjectName("PanelCard")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10), dp(self.scale, 10))
        panel_layout.setSpacing(dp(self.scale, 8))

        # 大按钮区：上传文件 / 选择输出路径
        self.btn_pick_pdf = QPushButton("上传文件")
        self.btn_pick_pdf.setMinimumHeight(dp(self.scale, 72))
        self.btn_pick_pdf.clicked.connect(self.on_pick_pdf)

        self.btn_pick_output = QPushButton("选择输出路径")
        self.btn_pick_output.setMinimumHeight(dp(self.scale, 72))
        self.btn_pick_output.clicked.connect(self.on_pick_output)

        panel_layout.addWidget(self.btn_pick_pdf)

        # 选择后的展示：PDF 与输出路径（统一表单布局）
        self.pdf_path_edit = QLineEdit()
        self.pdf_path_edit.setReadOnly(True)
        self.pdf_path_edit.setPlaceholderText("已选择的 PDF 路径")
        self.pdf_path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        panel_layout.addWidget(self.btn_pick_output)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("输出 DOCX 路径")
        self.output_path_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        path_form = QFormLayout()
        path_form.setLabelAlignment(Qt.AlignRight)
        path_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        path_form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        path_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        path_form.setHorizontalSpacing(dp(self.scale, 8))
        path_form.setVerticalSpacing(dp(self.scale, 6))

        # 统一标签宽度，提升多页一致性
        label_w = dp(self.scale, 90)
        lbl_pdf = QLabel("PDF路径"); lbl_pdf.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lbl_pdf.setFixedWidth(label_w)
        lbl_out = QLabel("输出DOCX"); lbl_out.setAlignment(Qt.AlignRight | Qt.AlignVCenter); lbl_out.setFixedWidth(label_w)

        path_form.addRow(lbl_pdf, self.pdf_path_edit)
        path_form.addRow(lbl_out, self.output_path_edit)
        panel_layout.addLayout(path_form)

        # 操作按钮区
        ops = QHBoxLayout()
        ops.setSpacing(dp(self.scale, 6))

        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.setMinimumHeight(dp(self.scale, 36))
        self.btn_convert.clicked.connect(self.on_start_convert)

        self.btn_open = QPushButton("打开docx")
        self.btn_open.setMinimumHeight(dp(self.scale, 36))
        self.btn_open.clicked.connect(self.on_open_docx)

        self.btn_contact = QPushButton("联系我们")
        self.btn_contact.setMinimumHeight(dp(self.scale, 36))
        self.btn_contact.clicked.connect(self.on_contact)

        ops.addWidget(self.btn_convert)
        ops.addWidget(self.btn_open)
        ops.addWidget(self.btn_contact)
        panel_layout.addLayout(ops)

        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setMinimumHeight(dp(self.scale, 16))
        root.addWidget(self.progress)

        # 状态提示
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        root.addWidget(self.status_label)
        root.addWidget(panel)

    # --- QSS 样式 ---
    def _apply_style(self):
        self.setStyleSheet(build_style(self.scale))

    # 无标题栏拖拽
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and hasattr(self, "title_bar") and self.title_bar.rect().contains(event.pos()):
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

    def on_toggle_fullscreen(self):
        # 顶层窗口全屏/还原切换（嵌入时作用于主窗口）
        top = self if self.isWindow() else self.window()
        if top.isFullScreen():
            top.showNormal()
        else:
            top.showFullScreen()

    def on_set_size(self):
        top = self if self.isWindow() else self.window()
        w, ok1 = QInputDialog.getInt(self, "设置宽度", "宽度(px):", top.width(), 800, 3840, 10)
        if not ok1:
            return
        h, ok2 = QInputDialog.getInt(self, "设置高度", "高度(px):", top.height(), 600, 2160, 10)
        if not ok2:
            return
        top.resize(w, h)

    # --- 交互逻辑 ---
    def on_pick_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择需要转换的 PDF",
            os.path.join(BASE_DIR, "测试材料"),
            "PDF 文件 (*.pdf)"
        )
        if not path:
            return
        self.pdf_path = path
        self.btn_pick_pdf.setText(self._short_text(f"已选择: {os.path.basename(path)}"))
        self.btn_pick_pdf.setToolTip(path)
        # 展示在独立组件
        try:
            self.pdf_path_edit.setText(path)
        except Exception:
            pass
        # 自动建议输出路径
        self.docx_path = suggest_docx_path(path)
        self.btn_pick_output.setText(self._short_text(f"默认输出: {os.path.basename(self.docx_path)}"))
        self.btn_pick_output.setToolTip(self.docx_path)
        try:
            self.output_path_edit.setText(self.docx_path)
        except Exception:
            pass
        self.status_label.setText("已选择 PDF，可开始转换")

    def on_pick_output(self):
        if not self.pdf_path:
            QMessageBox.information(self, "提示", "请先选择 PDF 文件")
            return
        default = suggest_docx_path(self.pdf_path)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出 DOCX",
            default,
            "Word 文档 (*.docx)"
        )
        if not path:
            return
        self.docx_path = path
        self.btn_pick_output.setText(self._short_text(f"输出: {os.path.basename(path)}"))
        self.btn_pick_output.setToolTip(path)
        try:
            self.output_path_edit.setText(path)
        except Exception:
            pass

    def on_start_convert(self):
        if not self.pdf_path:
            QMessageBox.information(self, "提示", "请先选择 PDF 文件")
            return
        # 输出路径兜底
        if not self.docx_path:
            self.docx_path = suggest_docx_path(self.pdf_path)

        self.progress.setValue(0)
        self.status_label.setText("正在转换...")
        self._set_controls_enabled(False)

        self.worker = PDF2DOCXWorker(self.pdf_path, self.docx_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.success.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def on_open_docx(self):
        if not self.docx_path or not os.path.exists(self.docx_path):
            QMessageBox.information(self, "提示", "还没有可打开的 DOCX 文件")
            return
        try:
            os.startfile(self.docx_path)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    def on_contact(self):
        # 简单处理：弹出信息，或可改为打开链接/邮件。
        QMessageBox.information(
            self,
            "联系我们",
            "感谢使用！如需反馈，请在仓库提交 issue 或发送邮件。"
        )

    # --- 辅助 ---
    def _on_progress(self, pct: int, msg: str):
        self.progress.setValue(max(0, min(100, int(pct))))
        self.status_label.setText(msg)

    def _on_success(self, path: str):
        self.progress.setValue(100)
        self.status_label.setText("转换完成")
        self._set_controls_enabled(True)
        QMessageBox.information(self, "成功", f"已生成文件:\n{path}")

    def _on_failed(self, err: str):
        self._set_controls_enabled(True)
        self.status_label.setText("转换失败")
        QMessageBox.critical(self, "失败", err)

    def _set_controls_enabled(self, enabled: bool):
        for w in (self.btn_pick_pdf, self.btn_pick_output, self.btn_convert, self.btn_open, self.btn_contact):
            w.setEnabled(enabled)

    def _short_text(self, text: str, max_len: int = 38) -> str:
        return (text[:max_len] + "…") if len(text) > max_len else text


def main():
    # 高分屏适配
    try:
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    except Exception:
        pass

    app = QApplication(sys.argv)
    apply_base_font(app, compute_scale(app))
    w = PDF2DOCXWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()