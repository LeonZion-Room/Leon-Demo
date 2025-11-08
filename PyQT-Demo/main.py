#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import webbrowser
from typing import Optional

from PyQt6 import QtCore, QtWidgets, QtGui

# 将转换能力直接复用项目中的 pdf_fc.py
from pdf_fc import pdf2docx


CONTACT_URL = "https://www.example.com/"  # 点击“联系我们”时打开的地址，可按需修改


class ConverterWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal(str, str)  # (output_path, error_msg)
    progress = QtCore.pyqtSignal(int, str)  # (pct, msg)

    def __init__(self, pdf_path: str, output_path: Optional[str] = None) -> None:
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path

    @QtCore.pyqtSlot()
    def run(self) -> None:
        try:
            def cb(pct: int, msg: str) -> None:
                try:
                    self.progress.emit(int(pct), str(msg))
                except Exception:
                    pass

            out = pdf2docx(self.pdf_path, self.output_path, progress_cb=cb)
            self.finished.emit(out, "")
        except Exception as e:
            self.finished.emit("", str(e))


class MainWindow(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        # 无边框窗口
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.resize(1024, 420)

        self.drag_pos: Optional[QtCore.QPoint] = None
        self.pdf_path: str = ""
        self.output_path: str = ""
        self.last_output: str = ""

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background-color: #2b2b2b; color: #e0e0e0; font-family: 'Microsoft YaHei'; font-size: 16px; }
            QLabel#hdr, QLabel#subhdr { background-color: #111111; border-radius: 8px; padding: 6px; }
            QPushButton { background-color: #2c55a1; border-radius: 8px; padding: 12px; color: #ffffff; }
            QPushButton:hover { background-color: #3a6abc; }
            QPushButton:disabled { background-color: #555555; color: #aaaaaa; }
            QProgressBar { background-color: #1e1e1e; border: 1px solid #444; border-radius: 6px; text-align: center; height: 22px; }
            QProgressBar::chunk { background-color: #2f80ed; border-radius: 6px; }
            QFrame#card { background-color: #2f2f2f; border-radius: 10px; }
            """
        )

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)

        # 顶部自定义栏
        hdr = QtWidgets.QLabel("应用-1", self)
        hdr.setObjectName("hdr")
        hdr.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        hdr.setFixedHeight(40)
        root.addWidget(hdr)

        # 功能区标题
        subhdr = QtWidgets.QLabel("LZ-PDF 转 DOCX", self)
        subhdr.setObjectName("subhdr")
        subhdr.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subhdr.setFixedHeight(40)
        root.addWidget(subhdr)

        card = QtWidgets.QFrame(self)
        card.setObjectName("card")
        card_box = QtWidgets.QVBoxLayout(card)
        card_box.setContentsMargins(16, 16, 16, 16)
        card_box.setSpacing(14)
        root.addWidget(card)

        # 文件信息行
        info = QtWidgets.QFormLayout()
        info.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.lab_pdf = QtWidgets.QLabel("未选择", self)
        self.lab_output = QtWidgets.QLabel("未选择", self)
        info.addRow("PDF 文件:", self.lab_pdf)
        info.addRow("输出路径:", self.lab_output)
        card_box.addLayout(info)

        # 操作按钮
        self.btn_upload = QtWidgets.QPushButton("上传文件", self)
        self.btn_outdir = QtWidgets.QPushButton("选择输出路径", self)
        self.btn_convert = QtWidgets.QPushButton("开始转换", self)
        self.btn_open = QtWidgets.QPushButton("打开docx", self)
        self.btn_contact = QtWidgets.QPushButton("联系我们", self)

        card_box.addWidget(self.btn_upload)
        card_box.addWidget(self.btn_outdir)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.btn_convert)
        row.addWidget(self.btn_open)
        row.addWidget(self.btn_contact)
        card_box.addLayout(row)

        # 进度条
        self.progress = QtWidgets.QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        card_box.addWidget(self.progress)

        # 按钮状态与事件
        self.btn_open.setEnabled(False)
        self.btn_convert.setEnabled(False)

        self.btn_upload.clicked.connect(self.choose_pdf)
        self.btn_outdir.clicked.connect(self.choose_output)
        self.btn_convert.clicked.connect(self.start_convert)
        self.btn_contact.clicked.connect(lambda: webbrowser.open(CONTACT_URL))
        self.btn_open.clicked.connect(self.open_output)

    # 选择 PDF
    def choose_pdf(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择 PDF 文件", "", "PDF (*.pdf)")
        if path:
            self.pdf_path = path
            self.lab_pdf.setText(os.path.basename(path))
            self._update_convert_state()

    # 选择输出路径（保存为 .docx 文件）
    def choose_output(self) -> None:
        start_dir = os.path.dirname(self.pdf_path) if self.pdf_path else ""
        base = os.path.splitext(os.path.basename(self.pdf_path))[0] if self.pdf_path else "输出"
        default = os.path.join(start_dir, f"{base}.docx")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "选择输出路径", default, "Word 文档 (*.docx)")
        if path:
            self.output_path = path
            self.lab_output.setText(os.path.basename(path))
            self._update_convert_state()

    def _update_convert_state(self) -> None:
        self.btn_convert.setEnabled(bool(self.pdf_path))

    # 启动转换线程
    def start_convert(self) -> None:
        if not self.pdf_path:
            return

        self.progress.setValue(0)
        self.progress.setFormat("准备中…")
        self.btn_convert.setEnabled(False)
        self.btn_open.setEnabled(False)

        self.thread = QtCore.QThread(self)
        self.worker = ConverterWorker(self.pdf_path, self.output_path or None)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_progress(self, pct: int, msg: str) -> None:
        self.progress.setValue(int(pct))
        self.progress.setFormat(f"{pct}% - {msg}")

    def on_finished(self, output: str, err: str) -> None:
        if err:
            QtWidgets.QMessageBox.critical(self, "转换失败", err)
            self.btn_convert.setEnabled(True)
            self.progress.setFormat("转换失败")
            return

        self.last_output = output
        self.btn_open.setEnabled(bool(output))
        self.btn_convert.setEnabled(True)
        self.progress.setValue(100)
        self.progress.setFormat("完成")

    def open_output(self) -> None:
        if self.last_output and os.path.exists(self.last_output):
            os.startfile(self.last_output)

    # 让窗口可拖动
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.drag_pos and (event.buttons() & QtCore.Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        self.drag_pos = None


def run_app() -> None:
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()