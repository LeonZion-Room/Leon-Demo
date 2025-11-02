import sys
import os
import json
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QTextBrowser,
    QPushButton,
    QFileDialog,
    QSplitter,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QListView,
    QInputDialog,
    QStyle,
)


def get_base_dir() -> Path:
    # 当打包为 exe 时，使用 exe 所在目录；否则用脚本所在目录
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


class MarkdownEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.base_dir = get_base_dir()
        self.config_path = self.base_dir / "md_exe_config.json"
        self.default_md_path = self.base_dir / "document.md"
        self.frameless = False
        self._loading = True

        self.setWindowTitle("Markdown 实时预览")
        # 允许拖拽文件到窗口以自动存入，并确保 files 目录存在
        self.setAcceptDrops(True)
        self.files_dir = self.base_dir / "files"
        try:
            self.files_dir.mkdir(exist_ok=True)
        except Exception:
            pass

        # 主区域：左右分栏
        self.splitter = QSplitter(Qt.Horizontal)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("在此输入 Markdown 文本……")
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([500, 500])

        # 文件列表（底部显示，图标模式更醒目）
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.file_list.setViewMode(QListView.IconMode)
        self.file_list.setIconSize(QSize(40, 40))
        self.file_list.setSpacing(8)
        self.file_list.setResizeMode(QListView.Adjust)
        self.file_list.setMovement(QListView.Static)
        self.file_list.setWrapping(True)

        # 顶部编辑/预览 + 底部文件列表（可拖拽分割）
        self.vsplitter = QSplitter(Qt.Vertical)
        self.vsplitter.addWidget(self.splitter)
        self.vsplitter.addWidget(self.file_list)
        self.vsplitter.setSizes([700, 200])

        # 顶部工具行
        toolbar = QHBoxLayout()
        self.border_btn = QPushButton("切换边框")
        self.save_btn = QPushButton("保存到同目录")
        self.save_as_btn = QPushButton("另存为…")
        self.open_dir_btn = QPushButton("打开files目录")
        self.clear_files_btn = QPushButton("清空files")
        self.status_label = QLabel("")
        self.exit_btn = QPushButton("退出")
        self.rename_btn = QPushButton("重命名")

        toolbar.addWidget(self.border_btn)
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.save_as_btn)
        toolbar.addWidget(self.open_dir_btn)
        toolbar.addWidget(self.clear_files_btn)
        toolbar.addWidget(self.rename_btn)
        toolbar.addStretch(1)
        toolbar.addWidget(self.status_label)
        toolbar.addWidget(self.exit_btn)

        # 总布局
        root = QVBoxLayout()
        root.addLayout(toolbar)
        root.addWidget(self.vsplitter)
        self.setLayout(root)

        # 信号连接
        # 实时预览与自动保存（防抖 1s）
        self.editor.textChanged.connect(self.update_preview)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(1000)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self.do_autosave)
        self.editor.textChanged.connect(self.schedule_autosave)
        self.file_list.itemClicked.connect(self.open_file_item)
        self.border_btn.clicked.connect(self.toggle_border)
        self.save_btn.clicked.connect(self.save_default)
        self.save_as_btn.clicked.connect(self.save_as)
        self.exit_btn.clicked.connect(self.close)
        self.open_dir_btn.clicked.connect(self.open_files_folder)
        self.clear_files_btn.clicked.connect(self.clear_files_folder)
        self.rename_btn.clicked.connect(self.rename_selected_file)

        # 载入配置与初始状态
        self.load_config()
        self._loading = False
        self.update_preview()
        self.update_status()
        self.refresh_file_list()

    def update_preview(self):
        # 使用 Qt 的 Markdown 渲染
        self.preview.setMarkdown(self.editor.toPlainText())

    def toggle_border(self):
        # 切换是否无边框；无边框时锁定尺寸，避免鼠标调整大小
        self.frameless = not self.frameless
        if self.frameless:
            self.setWindowFlag(Qt.FramelessWindowHint, True)
            self.setWindowFlag(Qt.Window, True)
            self.setWindowFlag(Qt.WindowStaysOnBottomHint, True)
            self.show()  # 变更 flag 后需要 show
            self.setFixedSize(self.size())  # 锁定尺寸
        else:
            self.setWindowFlag(Qt.FramelessWindowHint, False)
            self.setWindowFlag(Qt.Window, True)
            self.setWindowFlag(Qt.WindowStaysOnBottomHint, True)
            self.show()
            # 解除尺寸锁定，允许自由调整大小
            self.setMinimumSize(400, 300)
            self.setMaximumSize(16777215, 16777215)  # Qt 的最大值
        self.update_status()

    def schedule_autosave(self):
        # 初次载入时不触发自动保存；输入时 1s 防抖保存到同目录
        if self._loading:
            return
        self.autosave_timer.start()

    def do_autosave(self):
        try:
            self.default_md_path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.status_label.setText(f"自动保存: {self.default_md_path.name}")
        except Exception as e:
            self.status_label.setText(f"自动保存失败: {e}")

    # 拖拽文件到窗口自动复制到 files 目录
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            return
        added = 0
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if not local_path:
                continue
            p = Path(local_path)
            if p.is_file():
                try:
                    dest = self.copy_incoming_file(p)
                    added += 1
                except Exception as e:
                    self.status_label.setText(f"拷贝失败: {e}")
        if added:
            self.refresh_file_list()
            self.status_label.setText(f"已添加 {added} 个文件到 files")

    def copy_incoming_file(self, src: Path) -> Path:
        self.files_dir.mkdir(exist_ok=True)
        dest = self.files_dir / src.name
        if dest.exists():
            stem = src.stem
            suffix = src.suffix
            i = 1
            while True:
                candidate = self.files_dir / f"{stem}_{i}{suffix}"
                if not candidate.exists():
                    dest = candidate
                    break
                i += 1
        shutil.copy2(str(src), str(dest))
        return dest

    def refresh_file_list(self):
        self.file_list.clear()
        if not self.files_dir.exists():
            return
        try:
            files = sorted([p for p in self.files_dir.iterdir() if p.is_file()], key=lambda x: x.name.lower())
            for p in files:
                item = QListWidgetItem(p.name)
                item.setData(Qt.UserRole, str(p))
                # 设置更显著的图标与提示
                try:
                    icon = QApplication.style().standardIcon(QStyle.SP_FileIcon)
                    item.setIcon(icon)
                    item.setToolTip(f"{p.name}\n大小: {p.stat().st_size} 字节")
                except Exception:
                    pass
                # Markdown 文件加粗显示
                try:
                    if p.suffix.lower() in {".md", ".markdown"}:
                        f = item.font()
                        f.setBold(True)
                        item.setFont(f)
                except Exception:
                    pass
                self.file_list.addItem(item)
        except Exception:
            pass

    def open_file_item(self, item: QListWidgetItem):
        path = Path(item.data(Qt.UserRole))
        if path.suffix.lower() in {".md", ".markdown"}:
            try:
                self.editor.setPlainText(path.read_text(encoding="utf-8"))
                self.update_preview()
                self.status_label.setText(f"已打开: {path.name}")
            except Exception as e:
                self.status_label.setText(f"打开失败: {e}")
        else:
            try:
                os.startfile(str(path))
            except Exception as e:
                self.status_label.setText(f"系统打开失败: {e}")

    def open_files_folder(self):
        try:
            os.startfile(str(self.files_dir))
        except Exception as e:
            self.status_label.setText(f"打开目录失败: {e}")

    def clear_files_folder(self):
        if not self.files_dir.exists():
            return
        removed = 0
        try:
            for p in list(self.files_dir.iterdir()):
                try:
                    if p.is_file():
                        p.unlink()
                        removed += 1
                    elif p.is_dir():
                        shutil.rmtree(str(p))
                        removed += 1
                except Exception:
                    pass
            self.refresh_file_list()
            self.status_label.setText(f"已清空 files，移除 {removed} 项")
        except Exception as e:
            self.status_label.setText(f"清空失败: {e}")

    def rename_selected_file(self):
        item = self.file_list.currentItem()
        if not item:
            self.status_label.setText("请先选择一个文件")
            return
        old_path = Path(item.data(Qt.UserRole))
        text, ok = QInputDialog.getText(self, "重命名", "新文件名：", text=old_path.name)
        if not ok:
            return
        new_name = text.strip()
        invalid_chars = set('<>:"/\\|?*')
        if not new_name or any(ch in invalid_chars for ch in new_name):
            self.status_label.setText("文件名不合法")
            return
        new_path = self.files_dir / new_name
        if new_path.exists():
            # 若重名，自动加序号
            stem = Path(new_name).stem
            suffix = Path(new_name).suffix
            i = 1
            while True:
                candidate = self.files_dir / f"{stem}_{i}{suffix}"
                if not candidate.exists():
                    new_path = candidate
                    break
                i += 1
        try:
            old_path.rename(new_path)
            self.refresh_file_list()
            self.status_label.setText(f"已重命名为: {new_path.name}")
        except Exception as e:
            self.status_label.setText(f"重命名失败: {e}")

    def update_status(self):
        self.status_label.setText(
            "无边框(不可调整)" if self.frameless else "有边框(可调整)"
        )

    def save_default(self):
        try:
            self.default_md_path.write_text(self.editor.toPlainText(), encoding="utf-8")
            self.status_label.setText(f"已保存: {self.default_md_path.name}")
        except Exception as e:
            self.status_label.setText(f"保存失败: {e}")

    def save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "另存为",
            str(self.base_dir / "document.md"),
            "Markdown 文件 (*.md);;所有文件 (*.*)",
        )
        if path:
            try:
                Path(path).write_text(self.editor.toPlainText(), encoding="utf-8")
                self.status_label.setText(f"已保存: {Path(path).name}")
            except Exception as e:
                self.status_label.setText(f"保存失败: {e}")

    def load_config(self):
        if self.config_path.exists():
            try:
                cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
                w, h = cfg.get("size", [900, 600])
                x, y = cfg.get("pos", [100, 100])
                self.frameless = bool(cfg.get("frameless", False))

                self.resize(w, h)
                self.move(x, y)

                if self.frameless:
                    self.setWindowFlag(Qt.FramelessWindowHint, True)
                    self.setWindowFlag(Qt.Window, True)
                    self.setWindowFlag(Qt.WindowStaysOnBottomHint, True)
                    self.show()
                    self.setFixedSize(self.size())
                else:
                    self.setWindowFlag(Qt.FramelessWindowHint, False)
                    self.setWindowFlag(Qt.Window, True)
                    self.setWindowFlag(Qt.WindowStaysOnBottomHint, True)
                    self.show()
                    self.setMinimumSize(400, 300)
                    self.setMaximumSize(16777215, 16777215)
            except Exception:
                # 配置损坏时走默认
                self.resize(900, 600)
        else:
            self.resize(900, 600)
            self.move(100, 100)
            # 默认置底
            self.setWindowFlag(Qt.WindowStaysOnBottomHint, True)

        # 载入已有文档内容
        try:
            if self.default_md_path.exists():
                text = self.default_md_path.read_text(encoding="utf-8")
                self.editor.setPlainText(text)
        except Exception:
            pass

    def closeEvent(self, event):
        # 关闭时保存窗口位置与尺寸和边框状态
        cfg = {
            "size": [self.width(), self.height()],
            "pos": [self.x(), self.y()],
            "frameless": self.frameless,
        }
        try:
            self.config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = MarkdownEditor()
    win.show()
    # 再次请求置底
    try:
        win.lower()
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()