import sys
import win32gui
import win32con
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

class EmbeddedWindow(QMainWindow):
    def __init__(self, target_hwnd):
        super().__init__()
        self.target_hwnd = target_hwnd  # 目标应用的窗口句柄
        self.init_ui()
        self.embed_target_window()

    def init_ui(self):
        """初始化PySide6窗口布局"""
        self.setWindowTitle("嵌入其他应用窗口示例")
        self.setGeometry(100, 100, 800, 600)  # 初始位置和大小

        # 创建中心容器（用于承载目标窗口）
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # 去掉容器边距

    def embed_target_window(self):
        """将目标窗口嵌入PySide6容器"""
        # 获取PySide6容器的HWND（Windows下winId()返回HWND的整数形式）
        pyside_hwnd = int(self.central_widget.winId())

        # 1. 设置目标窗口的父窗口为PySide6容器
        win32gui.SetParent(self.target_hwnd, pyside_hwnd)

        # 2. 修改目标窗口样式：移除标题栏、边框、最小化/最大化按钮等
        current_style = win32gui.GetWindowLong(self.target_hwnd, win32con.GWL_STYLE)
        current_style &= ~(
            win32con.WS_CAPTION        # 标题栏
            | win32con.WS_THICKFRAME   # 可调边框
            | win32con.WS_MINIMIZEBOX  # 最小化按钮
            | win32con.WS_MAXIMIZEBOX  # 最大化按钮
            | win32con.WS_SYSMENU      # 系统菜单（右键标题栏的菜单）
        )
        win32gui.SetWindowLong(self.target_hwnd, win32con.GWL_STYLE, current_style)

        # 3. 显示目标窗口并调整大小
        win32gui.ShowWindow(self.target_hwnd, win32con.SW_SHOW)
        self.resize_target_window()

    def resize_target_window(self):
        """同步目标窗口与PySide6容器的大小"""
        container_rect = self.central_widget.rect()
        # MoveWindow参数：句柄、x、y、宽、高、是否重绘
        win32gui.MoveWindow(self.target_hwnd, 0, 0, container_rect.width(), container_rect.height(), True)

    def resizeEvent(self, event):
        """PySide6窗口大小变化时，同步调整目标窗口"""
        super().resizeEvent(event)
        if self.target_hwnd:
            self.resize_target_window()

def get_window_hwnd_by_title(window_title: str):
    """通过窗口标题模糊匹配获取句柄"""
    hwnd_list = []
    def enum_windows_callback(hwnd, extra):
        if window_title in win32gui.GetWindowText(hwnd):
            hwnd_list.append(hwnd)
        return True  # 继续枚举
    
    win32gui.EnumWindows(enum_windows_callback, None)
    return hwnd_list[0] if hwnd_list else None

if __name__ == "__main__":
    # ========== 配置目标窗口 ==========
    # 替换为你要嵌入的应用窗口标题（比如"记事本"、"Chrome"）
    TARGET_WINDOW_TITLE = "微信"
    
    # 获取目标窗口句柄
    target_hwnd = get_window_hwnd_by_title(TARGET_WINDOW_TITLE)
    if not target_hwnd:
        print(f"未找到标题包含「{TARGET_WINDOW_TITLE}」的窗口")
        sys.exit(1)

    # 启动PySide6应用
    app = QApplication(sys.argv)
    main_window = EmbeddedWindow(target_hwnd)
    main_window.show()
    sys.exit(app.exec())