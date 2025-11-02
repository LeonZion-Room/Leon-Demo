import sys
import os
import json
import time

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QUrl, QSize
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage


# 当使用 PyInstaller 打包时，写入到 exe 所在目录；否则写入到脚本目录
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
HISTORY_PATH = os.path.join(BASE_DIR, 'history.json')


def load_config():
    default_cfg = {
        'initial_url': 'https://www.example.com',
        'borderless': False,
        'geometry': None,  # {x, y, w, h}
        'settings_collapsed': True,  # 默认显示为精简工具条
        'toolbar_compact': False,     # 默认使用文字/图文样式，取消纯图标模式
        'auto_compact': False,       # 默认关闭自动紧凑切换
        'topbar_height': 32,         # 顶部栏高度（像素），可拖拽调整并持久化
    }
    if not os.path.exists(CONFIG_PATH):
        # 配置文件不存在时自动创建在 exe 同目录
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return default_cfg
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        for k, v in default_cfg.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return default_cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'保存配置失败: {e}')

# --- 历史记录（位置、大小、网址） ---
def _read_history_events():
    if not os.path.exists(HISTORY_PATH):
        # 历史文件不存在时自动创建在 exe 同目录
        try:
            with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return []
    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'events' in data and isinstance(data['events'], list):
            return data['events']
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []

def _write_history_events(events):
    try:
        # 直接写为列表，保持简洁
        with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'保存历史失败: {e}')

def _append_history_entry(geometry: dict | None, url: str | None):
    events = _read_history_events()
    entry = {
        'ts': int(time.time() * 1000),
    }
    if geometry:
        entry['geometry'] = geometry
    if url:
        entry['url'] = url
    events.append(entry)
    # 可选：限制最大条目数以避免无限增长
    if len(events) > 5000:
        events = events[-2000:]
    _write_history_events(events)

def _get_last_history():
    events = _read_history_events()
    if events:
        return events[-1]
    return None


class ExternalLinkPage(QWebEnginePage):
    """拦截页面中的链接点击，改为用系统默认浏览器打开。"""

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if nav_type == QWebEnginePage.NavigationTypeLinkClicked:
            # 在默认浏览器中打开链接
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)

    def createWindow(self, _type):
        # 处理 target=_blank 或 JS window.open 等新窗口请求
        new_page = QWebEnginePage(self)
        def _open(url):
            if url and not url.isEmpty():
                QDesktopServices.openUrl(url)
            # 释放临时页面
            new_page.deleteLater()
        new_page.urlChanged.connect(_open)
        return new_page


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, current_url: str, borderless: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.setModal(True)

        self.url_edit = QtWidgets.QLineEdit(self)
        self.url_edit.setText(current_url)
        self.url_edit.setPlaceholderText('https://...')

        self.borderless_check = QtWidgets.QCheckBox('无边框（无法用鼠标调整大小）', self)
        self.borderless_check.setChecked(borderless)

        form = QtWidgets.QFormLayout()
        form.addRow('初始网页地址', self.url_edit)
        form.addRow('窗口样式', self.borderless_check)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self):
        return self.url_edit.text().strip(), self.borderless_check.isChecked()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config

        self.setWindowTitle('Web Home Page Demo')
        self.resize(1000, 700)

        # 轻量防抖计时器，用于保存几何信息
        self._geometry_timer = QtCore.QTimer(self)
        self._geometry_timer.setSingleShot(True)
        self._geometry_timer.setInterval(400)
        self._geometry_timer.timeout.connect(self._flush_geometry)

        # 历史记录写入防抖（避免拖动时过于频繁写入）
        self._history_timer = QtCore.QTimer(self)
        self._history_timer.setSingleShot(True)
        self._history_timer.setInterval(350)
        self._history_timer.timeout.connect(self._append_history_snapshot)

        # Web 视图
        self.view = QWebEngineView(self)
        self.page = ExternalLinkPage(self.view)
        self.view.setPage(self.page)

        # 中心布局：顶部设置栏/精简工具条（堆栈） + 下方网页视图（垂直分割，支持拖拽调整顶部高度）
        self.settings_bar = self._build_settings_bar()
        self.collapsed_toolbar = self._build_collapsed_toolbar()
        self.top_bar_stack = QtWidgets.QStackedWidget(self)
        self.top_bar_stack.addWidget(self.settings_bar)
        self.top_bar_stack.addWidget(self.collapsed_toolbar)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(6)
        self.splitter.addWidget(self.top_bar_stack)
        self.splitter.addWidget(self.view)
        self.setCentralWidget(self.splitter)

        # 启动时优先从历史记录恢复最近一次的几何与网址
        self._apply_last_history()

        # 安装全局事件过滤器：每次点击都自动保存配置（含几何）
        app_instance = QtWidgets.QApplication.instance()
        if app_instance is not None:
            app_instance.installEventFilter(self)

        # 按历史/配置载入初始网页
        self.view.setUrl(QUrl(self.config.get('initial_url', 'https://www.example.com')))

        # 先恢复或定位到底部，再应用窗口样式
        self._restore_geometry_or_place_bottom()
        self._apply_window_chrome()

        # 初始化顶部堆栈显示、应用工具条样式与顶部栏高度
        if bool(self.config.get('settings_collapsed')):
            self.top_bar_stack.setCurrentWidget(self.collapsed_toolbar)
        else:
            self.top_bar_stack.setCurrentWidget(self.settings_bar)
        self._apply_toolbar_style()
        self._apply_initial_topbar_height()
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

    # --- 窗口样式与大小控制 ---
    def _apply_window_chrome(self):
        borderless = bool(self.config.get('borderless'))
        # 记录当前几何，确保切换前后位置与大小不变
        rect = self.geometry()

        # 切换是否无边框
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint, borderless)

        # 根据是否无边框决定是否允许改变大小，但保持当前尺寸
        if borderless:
            # 无边框：锁定当前大小，不允许鼠标调整
            self.setFixedSize(rect.width(), rect.height())
        else:
            # 有边框：允许调整大小
            self.setMinimumSize(600, 400)
            self.setMaximumSize(QtCore.QSize(16777215, 16777215))

        # 重新应用窗口标志并恢复几何
        self.show()
        self.setGeometry(rect)
        # 切换完成后立即持久化几何
        self._flush_geometry()
        # 同步写入历史记录
        self._append_history_snapshot()

    # --- 顶部设置栏（可收起） ---
    def _build_settings_bar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QFrame(self)
        bar.setFrameShape(QtWidgets.QFrame.StyledPanel)
        bar.setObjectName('settingsBar')
        bar.setStyleSheet('#settingsBar { background: #000000; }')

        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        title = QtWidgets.QLabel('设置', bar)
        title.setStyleSheet('font-weight: bold;')

        url_edit = QtWidgets.QLineEdit(bar)
        url_edit.setPlaceholderText('https://...')
        url_edit.setText(self.config.get('initial_url', ''))
        url_edit.setMinimumWidth(100)

        btn_apply_url = QtWidgets.QPushButton('应用网址', bar)
        btn_apply_url.clicked.connect(lambda: self._apply_url(url_edit.text().strip()))

        btn_toggle_borderless = QtWidgets.QPushButton('切换无边框', bar)
        btn_toggle_borderless.clicked.connect(self.toggle_borderless)

        btn_open_external = QtWidgets.QPushButton('用浏览器打开当前页', bar)
        btn_open_external.clicked.connect(self.open_current_in_browser)

        btn_minimize = QtWidgets.QPushButton('最小化', bar)
        btn_minimize.clicked.connect(self.showMinimized)

        btn_exit = QtWidgets.QPushButton('退出', bar)
        btn_exit.clicked.connect(QtWidgets.QApplication.quit)

        # 收起按钮
        btn_collapse = QtWidgets.QToolButton(bar)
        # btn_collapse.setText('收起')
        # btn_collapse.clicked.connect(self._collapse_settings_bar)

        # 排列
        layout.addWidget(title)
        layout.addWidget(url_edit, 1)
        layout.addWidget(btn_apply_url)
        layout.addWidget(btn_toggle_borderless)
        layout.addWidget(btn_open_external)
        layout.addWidget(btn_minimize)
        layout.addWidget(btn_exit)
        layout.addWidget(btn_collapse)

        return bar

    def _build_collapsed_toolbar(self) -> QtWidgets.QToolBar:
        tb = QtWidgets.QToolBar('精简工具条', self)
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        tb.setStyleSheet('QToolBar { padding: 2px; background: #f5f5f7; }')

        act_expand = QtGui.QAction('展开设置栏', self)
        act_expand.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowDown))
        act_expand.triggered.connect(self._expand_settings_bar)

        act_open_external = QtGui.QAction('外部打开当前页', self)
        act_open_external.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton))
        act_open_external.setToolTip('用系统浏览器打开当前页面')
        act_open_external.triggered.connect(self.open_current_in_browser)

        act_toggle_borderless = QtGui.QAction('切换无边框', self)
        act_toggle_borderless.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarShadeButton))
        act_toggle_borderless.setToolTip('在无边框与可调整大小之间切换')
        act_toggle_borderless.triggered.connect(self.toggle_borderless)

        act_minimize = QtGui.QAction('最小化', self)
        act_minimize.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarMinButton))
        act_minimize.triggered.connect(self.showMinimized)

        act_exit = QtGui.QAction('退出', self)
        act_exit.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton))
        act_exit.triggered.connect(QtWidgets.QApplication.quit)

        act_toggle_style = QtGui.QAction('切换样式', self)
        act_toggle_style.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
        act_toggle_style.setToolTip('在图标模式（更薄）与文字模式之间切换')
        act_toggle_style.triggered.connect(lambda: self._set_toolbar_compact(not bool(self.config.get('toolbar_compact'))))

        act_toggle_auto = QtGui.QAction('自动缩放', self)
        act_toggle_auto.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        act_toggle_auto.setToolTip('根据窗口宽度自动切换工具条样式')
        act_toggle_auto.triggered.connect(self._toggle_auto_compact)

        tb.addAction(act_expand)
        tb.addSeparator()
        tb.addAction(act_open_external)
        tb.addAction(act_toggle_borderless)
        tb.addAction(act_minimize)
        tb.addAction(act_exit)
        tb.addSeparator()
        tb.addAction(act_toggle_style)
        tb.addAction(act_toggle_auto)
        return tb

    def _collapse_settings_bar(self, save: bool = True):
        # 记录切换前的窗口几何与分割器尺寸，确保切换后尺寸不变
        prev_rect = self.geometry()
        sizes = self.splitter.sizes()
        top_h = sizes[0] if sizes else self.top_bar_stack.height()
        total = sum(sizes) if sizes else self.height()

        self.top_bar_stack.setCurrentWidget(self.collapsed_toolbar)

        # 恢复切换前的分割器尺寸与窗口几何
        self.splitter.setSizes([top_h, max(1, total - top_h)])
        self.setGeometry(prev_rect)

        if save:
            self.config['settings_collapsed'] = True
            # 持久化顶部栏高度避免样式提示导致高度变更
            self.config['topbar_height'] = int(top_h)
            save_config(self.config)

    def _expand_settings_bar(self):
        # 记录切换前的窗口几何与分割器尺寸，确保切换后尺寸不变
        prev_rect = self.geometry()
        sizes = self.splitter.sizes()
        top_h = sizes[0] if sizes else self.top_bar_stack.height()
        total = sum(sizes) if sizes else self.height()

        self.top_bar_stack.setCurrentWidget(self.settings_bar)

        # 恢复切换前的分割器尺寸与窗口几何
        self.splitter.setSizes([top_h, max(1, total - top_h)])
        self.setGeometry(prev_rect)

        self.config['settings_collapsed'] = False
        self.config['topbar_height'] = int(top_h)
        save_config(self.config)

    # --- 工具条样式与自动缩放 ---
    def _apply_toolbar_style(self):
        compact = bool(self.config.get('toolbar_compact'))
        if compact:
            self.collapsed_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            self.collapsed_toolbar.setIconSize(QSize(14, 14))
            self.collapsed_toolbar.setStyleSheet('QToolBar { padding: 1px; background: #f5f5f7; }')
        else:
            self.collapsed_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            self.collapsed_toolbar.setIconSize(QSize(18, 18))
            self.collapsed_toolbar.setStyleSheet('QToolBar { padding: 2px; background: #f5f5f7; }')

    def _apply_initial_topbar_height(self):
        # 根据配置设置初始顶部栏高度，并按高度调整图标尺寸
        try:
            top_h = int(self.config.get('topbar_height') or 32)
        except Exception:
            top_h = 32
        total_h = max(self.height(), 500)
        self.splitter.setSizes([top_h, max(200, total_h - top_h)])
        self._update_toolbar_scale_by_height(top_h)

    def _on_splitter_moved(self, pos: int, index: int):
        # 保存顶部栏高度并根据高度调整工具条图标尺寸
        top_h = self.top_bar_stack.height()
        self.config['topbar_height'] = int(top_h)
        save_config(self.config)
        self._update_toolbar_scale_by_height(top_h)

    def _set_toolbar_compact(self, compact: bool, persist: bool = True):
        self.config['toolbar_compact'] = bool(compact)
        self._apply_toolbar_style()
        if persist:
            save_config(self.config)

    def _toggle_auto_compact(self):
        self.config['auto_compact'] = not bool(self.config.get('auto_compact'))
        save_config(self.config)

    def _auto_adjust_toolbar_style(self):
        if bool(self.config.get('auto_compact')):
            width = self.width()
            threshold = 900
            if width < threshold:
                # 临时进入紧凑样式，不持久化
                self._apply_toolbar_style_temp(True)
            else:
                # 恢复用户偏好
                self._apply_toolbar_style()

    def _update_toolbar_scale_by_height(self, height: int):
        """根据顶部栏高度调整精简工具条图标大小，使“高度可调”直观生效。"""
        if height <= 0:
            return
        size = max(12, min(32, int(height) - 8))
        self.collapsed_toolbar.setIconSize(QSize(size, size))

    def _apply_toolbar_style_temp(self, compact: bool):
        # 不改变配置，仅临时调整显示
        if compact:
            self.collapsed_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            self.collapsed_toolbar.setIconSize(QSize(14, 14))
            self.collapsed_toolbar.setStyleSheet('QToolBar { padding: 1px; background: #f5f5f7; }')
        else:
            self.collapsed_toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            self.collapsed_toolbar.setIconSize(QSize(18, 18))
            self.collapsed_toolbar.setStyleSheet('QToolBar { padding: 2px; background: #f5f5f7; }')

    def _apply_last_history(self):
        last = _get_last_history()
        if not last:
            return
        # 恢复最近一次网址
        url = last.get('url')
        if isinstance(url, str) and url:
            self.config['initial_url'] = url
        # 恢复最近一次几何
        g = last.get('geometry')
        if isinstance(g, dict) and all(k in g for k in ('x', 'y', 'w', 'h')):
            try:
                self.config['geometry'] = {
                    'x': int(g['x']),
                    'y': int(g['y']),
                    'w': int(g['w']),
                    'h': int(g['h']),
                }
            except Exception:
                pass

    def _apply_url(self, text: str):
        if text:
            self.config['initial_url'] = text
            save_config(self.config)
            self.view.setUrl(QUrl(text))
            # 记录此次网址变更（附带当前几何）
            self._append_history_snapshot()

    def toggle_borderless(self):
        self.config['borderless'] = not bool(self.config.get('borderless'))
        save_config(self.config)
        self._apply_window_chrome()

    def open_current_in_browser(self):
        url = self.view.url()
        if url and not url.isEmpty():
            QDesktopServices.openUrl(url)

    # --- 设置对话框 ---
    def open_settings(self):
        dlg = SettingsDialog(
            current_url=self.config.get('initial_url', ''),
            borderless=bool(self.config.get('borderless')),
            parent=self,
        )
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            new_url, new_borderless = dlg.values()
            if new_url:
                self.config['initial_url'] = new_url
                self.view.setUrl(QUrl(new_url))
            self.config['borderless'] = bool(new_borderless)
            save_config(self.config)
            self._apply_window_chrome()

    # --- 启动定位与几何持久化 ---
    def _restore_geometry_or_place_bottom(self):
        g = self.config.get('geometry')
        if isinstance(g, dict) and all(k in g for k in ('x', 'y', 'w', 'h')):
            rect = QtCore.QRect(int(g['x']), int(g['y']), int(g['w']), int(g['h']))
            self.setGeometry(rect)
        else:
            # 无记录时，放置到屏幕底部居中
            screen = QtWidgets.QApplication.primaryScreen()
            if screen:
                avail = screen.availableGeometry()
                w, h = self.width(), self.height()
                x = avail.x() + (avail.width() - w) // 2
                y = avail.y() + (avail.height() - h)
                self.move(x, y)

    def _schedule_geometry_save(self):
        self._geometry_timer.start()

    def _flush_geometry(self):
        rect = self.geometry()
        self.config['geometry'] = {
            'x': rect.x(),
            'y': rect.y(),
            'w': rect.width(),
            'h': rect.height(),
        }
        save_config(self.config)

    def moveEvent(self, event: QtGui.QMoveEvent):
        super().moveEvent(event)
        # 每次移动立即保存几何
        self._flush_geometry()
        # 防抖写入历史
        self._history_timer.start()

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        # 每次缩放立即保存几何
        self._flush_geometry()
        self._auto_adjust_toolbar_style()
        # 防抖写入历史
        self._history_timer.start()

    def closeEvent(self, event: QtGui.QCloseEvent):
        # 关闭前强制保存最后一次位置与大小
        try:
            self._flush_geometry()
            # 同步追加一次历史快照
            self._append_history_snapshot()
        except Exception:
            pass
        super().closeEvent(event)

    def _append_history_snapshot(self):
        # 获取当前几何与网址
        rect = self.geometry()
        geometry = {
            'x': rect.x(),
            'y': rect.y(),
            'w': rect.width(),
            'h': rect.height(),
        }
        url = ''
        try:
            qurl = self.view.url()
            if qurl and not qurl.isEmpty():
                url = qurl.toString()
        except Exception:
            pass
        _append_history_entry(geometry=geometry, url=url)

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:
        # 任何一次鼠标按下都立即保存配置（几何等）
        if event.type() == QtCore.QEvent.MouseButtonPress:
            try:
                # 优先写入最新几何
                self._flush_geometry()
                # 如果其它字段有变化，也一并持久化
                save_config(self.config)
            except Exception:
                pass
        return False


def main():
    app = QtWidgets.QApplication(sys.argv)

    cfg = load_config()
    win = MainWindow(cfg)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()