import sys
import argparse
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QScrollArea,
    QFrame,
    QPushButton,
    QStyle,
    QLayout,
    QLabel,
    QSlider,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, QSize, QEvent, QTimer

from ui_style_nb import build_style, compute_scale, apply_base_font, dp
from pdf_split import PDFSplitWindow
from pdf2images import PdfToImagesWindow
from pdf2docx import PDF2DOCXWindow
from pdf_merge import PDFMergeWindow
from img2pdf import Img2PDFWindow


class MainWindow(QWidget):
    def __init__(self, scale: Optional[float] = None):
        super().__init__()
        self.setWindowTitle("PDF工具集")
        # 无边框主窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.scale = scale if scale is not None else compute_scale(QApplication.instance())

        self._build_ui()
        self.setStyleSheet(build_style(self.scale))

        # 简单拖动支持（无系统边框时）
        self._drag_pos: Optional[object] = None

    def _build_ui(self):
        # 根布局改为垂直，以便在最顶部放置可拖动细条
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(
            dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12)
        )
        self.root_layout.setSpacing(dp(self.scale, 8))
        # 让窗口最小/最大尺寸受布局 hint 约束，便于后续 adjustSize
        self.root_layout.setSizeConstraint(QLayout.SetMinAndMaxSize)

        # 顶部拖动条（细条），按住可拖动窗口位置
        self.drag_bar = QFrame()
        self.drag_bar.setObjectName("DragBar")
        self.drag_bar.setFixedHeight(dp(self.scale, 20))
        try:
            self.drag_bar.setCursor(Qt.SizeAllCursor)
        except Exception:
            pass
        self.root_layout.addWidget(self.drag_bar)

        # 左侧栏（菜单 + 尺寸控制）
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(dp(self.scale, 8))

        # 显示尺寸控制卡片（置于左栏顶部）
        self.scale_card = QFrame()
        self.scale_card.setObjectName("PanelCard")
        scale_layout = QVBoxLayout(self.scale_card)
        scale_layout.setContentsMargins(dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8))
        scale_layout.setSpacing(dp(self.scale, 6))

        scale_title = QLabel("显示尺寸")
        scale_title.setToolTip("调整界面缩放比例（0.65x - 1.80x）")
        scale_layout.addWidget(scale_title)

        row = QHBoxLayout()
        row.setSpacing(dp(self.scale, 6))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(65, 180)
        self.scale_slider.setSingleStep(5)
        self.scale_slider.setPageStep(5)
        self.scale_slider.setValue(int(round(self.scale * 100)))
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.65, 1.80)
        self.scale_spin.setSingleStep(0.05)
        self.scale_spin.setDecimals(2)
        self.scale_spin.setValue(round(self.scale, 2))
        self.scale_spin.setSuffix("x")
        row.addWidget(self.scale_slider, 1)
        row.addWidget(self.scale_spin)
        scale_layout.addLayout(row)
        left_layout.addWidget(self.scale_card)

        # 菜单列表（居中显示）
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(dp(self.scale, 160))
        self.sidebar.setUniformItemSizes(True)
        for name in ("PDF合并", "PDF拆分", "PDF转图片", "图片转PDF", "PDF转DOCX"):
            item = QListWidgetItem(name)
            item.setTextAlignment(Qt.AlignCenter)
            self.sidebar.addItem(item)
        # 顶部与底部留白以使菜单居中
        left_layout.addStretch(1)
        left_layout.addWidget(self.sidebar, 0, alignment=Qt.AlignCenter)
        left_layout.addStretch(1)

        # 底部退出按钮
        self.btn_quit = QPushButton("退出应用")
        try:
            style = self.style()
            self.btn_quit.setIcon(style.standardIcon(QStyle.SP_TitleBarCloseButton))
            self.btn_quit.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        except Exception:
            pass
        self.btn_quit.clicked.connect(QApplication.instance().quit)
        left_layout.addWidget(self.btn_quit)

        # 右侧：控制栏 + 功能栈
        self.stack = QStackedWidget()

        # 创建各功能页面并作为子部件嵌入
        self.page_merge = PDFMergeWindow(scale=self.scale, embedded=True)
        self.page_merge.setWindowFlags(Qt.Widget)

        self.page_split = PDFSplitWindow(scale=self.scale, embedded=True)
        self.page_split.setWindowFlags(Qt.Widget)

        self.page_images = PdfToImagesWindow(scale=self.scale, embedded=True)
        self.page_images.setWindowFlags(Qt.Widget)

        self.page_img2pdf = Img2PDFWindow(scale=self.scale, embedded=True)
        self.page_img2pdf.setWindowFlags(Qt.Widget)

        self.page_docx = PDF2DOCXWindow(scale=self.scale, embedded=True)
        self.page_docx.setWindowFlags(Qt.Widget)

        # 直接将页面加入栈（避免内层滚动嵌套导致滑杆不可拖动）
        self.stack.addWidget(self.page_merge)
        self.stack.addWidget(self.page_split)
        self.stack.addWidget(self.page_images)
        self.stack.addWidget(self.page_img2pdf)
        self.stack.addWidget(self.page_docx)

        # 顶部控制：全屏 / 退出全屏
        self.ctrl_bar = QHBoxLayout()
        self.ctrl_bar.setSpacing(dp(self.scale, 6))
        btn_full = QPushButton("设为全屏")
        btn_exit_full = QPushButton("退出全屏")
        style = self.style()
        try:
            btn_full.setIcon(style.standardIcon(QStyle.SP_TitleBarMaxButton))
            btn_full.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
            btn_exit_full.setIcon(style.standardIcon(QStyle.SP_TitleBarNormalButton))
            btn_exit_full.setIconSize(QSize(dp(self.scale, 18), dp(self.scale, 18)))
        except Exception:
            pass
        btn_full.clicked.connect(self.showFullScreen)
        btn_exit_full.clicked.connect(self.showNormal)
        self.ctrl_bar.addWidget(btn_full)
        self.ctrl_bar.addWidget(btn_exit_full)

        # 右侧整体作为滚动面板，纵向超出时出现滑杆（类似浏览器）
        self.right_panel = QFrame()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(dp(self.scale, 8))
        self.right_layout.addLayout(self.ctrl_bar)
        self.right_layout.addWidget(self.stack)
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidget(self.right_panel)
        # 不随视口大小强制缩放子控件，保持内容的自然尺寸并通过滑杆承载溢出
        self.right_scroll.setWidgetResizable(False)
        self.right_scroll.setFrameShape(QFrame.NoFrame)
        self.right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 中部主行（左侧栏 + 右侧内容）
        self.main_row = QHBoxLayout()
        self.main_row.setSpacing(dp(self.scale, 8))
        self.main_row.addWidget(left_panel)
        self.main_row.addWidget(self.right_scroll, 1)
        self.root_layout.addLayout(self.main_row, 1)

        # 绑定缩放组件事件
        self.scale_slider.valueChanged.connect(self._on_scale_slider)
        self.scale_spin.valueChanged.connect(self._on_scale_spin)

        self.sidebar.currentRowChanged.connect(self._on_sidebar_change)
        self.sidebar.setCurrentRow(0)
        # 监听内容布局变化，动态调整窗口尺寸
        self._install_resize_watch(self.page_merge)
        self._install_resize_watch(self.page_split)
        self._install_resize_watch(self.page_images)
        self._install_resize_watch(self.page_img2pdf)
        self._install_resize_watch(self.page_docx)
        # 移除对内层滚动包裹器的监听，统一监听页面本身

        # 初始按当前页内容估算窗口尺寸
        self._resize_to_page(0)

    def _on_scale_slider(self, value: int):
        new_scale = round(value / 100.0, 2)
        # 防止互相递归触发
        try:
            self.scale_spin.blockSignals(True)
            self.scale_spin.setValue(new_scale)
        finally:
            self.scale_spin.blockSignals(False)
        self._apply_scale(new_scale)

    def _on_scale_spin(self, value: float):
        new_val = int(round(float(value) * 100))
        try:
            self.scale_slider.blockSignals(True)
            self.scale_slider.setValue(new_val)
        finally:
            self.scale_slider.blockSignals(False)
        self._apply_scale(float(value))

    def _apply_scale(self, new_scale: float):
        # 更新主窗口的缩放与样式
        self.scale = float(max(0.65, min(1.80, new_scale)))
        app = QApplication.instance()
        try:
            apply_base_font(app, self.scale)
        except Exception:
            pass
        try:
            self.setStyleSheet(build_style(self.scale))
        except Exception:
            pass

        # 更新主布局参数与侧栏宽度
        try:
            self.root_layout.setContentsMargins(
                dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12), dp(self.scale, 12)
            )
            self.root_layout.setSpacing(dp(self.scale, 8))
            self.main_row.setSpacing(dp(self.scale, 8))
            self.drag_bar.setFixedHeight(dp(self.scale, 20))
            self.sidebar.setFixedWidth(dp(self.scale, 160))
            self.ctrl_bar.setSpacing(dp(self.scale, 6))
            self.right_layout.setSpacing(dp(self.scale, 8))
            # 更新缩放卡片内部间距
            self.scale_card.layout().setContentsMargins(
                dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8), dp(self.scale, 8)
            )
            self.scale_card.layout().setSpacing(dp(self.scale, 6))
        except Exception:
            pass

        # 更新各页面的缩放样式
        try:
            # PDF 合并页
            self.page_merge.scale = self.scale
            if hasattr(self.page_merge, "_apply_style"):
                self.page_merge._apply_style()
            else:
                self.page_merge.setStyleSheet(build_style(self.scale))
        except Exception:
            pass
        try:
            # PDF 拆分页
            self.page_split.scale = self.scale
            if hasattr(self.page_split, "_apply_style"):
                self.page_split._apply_style()
            else:
                self.page_split.setStyleSheet(build_style(self.scale))
        except Exception:
            pass
        try:
            # PDF 转图片页
            self.page_images.scale = self.scale
            if hasattr(self.page_images, "_apply_style"):
                self.page_images._apply_style()
            else:
                self.page_images.setStyleSheet(build_style(self.scale))
            # 在缩放变化时，主动刷新页面的自适应控件尺寸
            if hasattr(self.page_images, "_apply_responsive_sizes"):
                try:
                    self.page_images._apply_responsive_sizes()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            # 图片转 PDF 页
            self.page_img2pdf.scale = self.scale
            if hasattr(self.page_img2pdf, "_apply_style"):
                self.page_img2pdf._apply_style()
            else:
                self.page_img2pdf.setStyleSheet(build_style(self.scale))
            # 在缩放变化时，主动刷新页面的自适应控件尺寸
            if hasattr(self.page_img2pdf, "_apply_responsive_sizes"):
                try:
                    self.page_img2pdf._apply_responsive_sizes()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            # PDF 转 DOCX 页
            self.page_docx.scale = self.scale
            if hasattr(self.page_docx, "_apply_style"):
                self.page_docx._apply_style()
            else:
                self.page_docx.setStyleSheet(build_style(self.scale))
        except Exception:
            pass

        # 触发自动调整（保留“仅增大”策略）
        self._schedule_resize()

    def _on_sidebar_change(self, index: int):
        self.stack.setCurrentIndex(index)
        self._resize_to_page(index)

    def _install_resize_watch(self, w: QWidget):
        try:
            w.installEventFilter(self)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        try:
            if event.type() in (QEvent.LayoutRequest, QEvent.Resize, QEvent.Show):
                self._schedule_resize()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    def _schedule_resize(self):
        # 全屏时跳过自动缩放，避免与用户意图冲突
        if self.isFullScreen():
            return
        if getattr(self, "_resize_pending", False):
            return
        self._resize_pending = True
        QTimer.singleShot(50, self._do_resize)

    def _do_resize(self):
        self._resize_pending = False
        self._resize_to_page(self.stack.currentIndex())

    def _resize_to_page(self, index: int):
        try:
            wrapper = self.stack.widget(index)
            content = wrapper.widget() if isinstance(wrapper, QScrollArea) else wrapper
            hint = content.sizeHint()
            # 计算左右边距与侧栏宽度
            m = self.layout().contentsMargins()
            # 水平间距来自主行布局
            spacing = getattr(self, "main_row", self.layout()).spacing()
            left_w = self.sidebar.width() or self.sidebar.sizeHint().width()
            target_w = hint.width() + left_w + spacing + m.left() + m.right()
            target_h = hint.height() + m.top() + m.bottom()
            # 屏幕约束与最小值（仅增不减）
            screen = QApplication.instance().primaryScreen()
            min_w = dp(self.scale, 840)
            min_h = dp(self.scale, 520)
            cur_w, cur_h = self.width(), self.height()
            if screen:
                ag = screen.availableGeometry()
                max_w = int(ag.width() * 0.95)
                max_h = int(ag.height() * 0.92)
                # 宽度：在不超过屏幕的前提下，按内容需要增大；避免水平滚动条
                new_w = min(max(cur_w, max(target_w, min_w)), max_w)
                # 高度：保持当前高度（如浏览器一样用垂直滚动容器承载超出内容），只在过小/过大时收敛到合理范围
                new_h = min(max(cur_h if cur_h > 0 else min_h, min_h), max_h)
            else:
                new_w = max(cur_w, max(target_w, min_w))
                new_h = max(cur_h if cur_h > 0 else min_h, min_h)
            # 调整宽度；高度仅在超出合理范围时调整，日常保持稳定以依赖滚动条承载溢出
            if new_w != cur_w or new_h != cur_h:
                self.resize(new_w, new_h)
        except Exception:
            pass

    def mousePressEvent(self, event):
        # 仅当点击顶部拖动条时，进入拖动模式
        if event.button() == Qt.LeftButton and hasattr(self, "drag_bar"):
            try:
                if self.drag_bar.geometry().contains(event.pos()):
                    self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
                    return
            except Exception:
                pass
        self._drag_pos = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


def main():
    # 高分屏适配
    try:
        from PyQt5 import QtCore
        QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="PDF工具集主程序")
    parser.add_argument("--scale", type=float, default=None, help="界面缩放比例，例如 1.0、1.25")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    scale = args.scale if args.scale is not None else compute_scale(app)
    apply_base_font(app, scale)

    w = MainWindow(scale=scale)
    # 自动适配屏幕：初始尺寸按可用区域比例设置
    screen = app.primaryScreen()
    try:
        ag = screen.availableGeometry()
        init_w = max(dp(scale, 840), int(ag.width() * 0.72))
        init_h = max(dp(scale, 520), int(ag.height() * 0.66))
        w.resize(init_w, init_h)
    except Exception:
        w.resize(dp(scale, 960), dp(scale, 600))
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()