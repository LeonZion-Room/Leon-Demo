import os
import sys
import json
import difflib
import time
from PySide6.QtCore import Qt, QUrl, QEvent, QTimer
from PySide6.QtGui import QColor, QPainter, QDesktopServices, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QSlider, QColorDialog, QScrollArea, QFrame, QSpinBox, QDialog, QFormLayout, QDialogButtonBox, QCheckBox, QStyle, QSystemTrayIcon, QMenu, QMessageBox, QPlainTextEdit, QTabWidget, QInputDialog
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineProfile, QWebEngineSettings
try:
    import win32gui
    import win32con
except Exception:
    win32gui = None
    win32con = None
try:
    from shiboken6 import isValid
except Exception:
    def isValid(obj):
        try:
            return obj is not None
        except Exception:
            return False

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
 
def get_user_data_dir():
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
        return os.path.join(base, 'CardGrid')
    return os.path.join(os.path.expanduser('~'), '.cardgrid')
DATA_DIR = get_user_data_dir()
LAYOUT_PATH = os.path.join(BASE_DIR, 'layout.json')

def ensure_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LAYOUT_PATH):
        try:
            base = getattr(sys, '_MEIPASS', BASE_DIR)
            cand = [
                os.path.join(base, 'pyside_exe_card', 'data', 'layout.json'),
                os.path.join(BASE_DIR, 'pyside_exe_card', 'data', 'layout.json'),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'layout.json')
            ]
            for src in cand:
                if os.path.exists(src):
                    with open(src, 'r', encoding='utf-8') as f:
                        d = json.load(f)
                    with open(LAYOUT_PATH, 'w', encoding='utf-8') as g:
                        json.dump(d, g, ensure_ascii=False, indent=2)
                    break
            else:
                with open(LAYOUT_PATH, 'w', encoding='utf-8') as f:
                    json.dump({"locked": False, "items": []}, f, ensure_ascii=False, indent=2)
        except Exception:
            with open(LAYOUT_PATH, 'w', encoding='utf-8') as f:
                json.dump({"locked": False, "items": []}, f, ensure_ascii=False, indent=2)

def load_layout():
    ensure_data()
    with open(LAYOUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_layout(data):
    with open(LAYOUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Page(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        pass
    def acceptNavigationRequest(self, url, nav_type, isMainFrame):
        p = self.parent()
        if isinstance(p, CardWidget) and getattr(p, 'mode', 'in') == 'out' and isMainFrame:
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, nav_type, isMainFrame)

    def createWindow(self, type):
        p = self.parent()
        if isinstance(p, CardWidget):
            if getattr(p, 'mode', 'in') == 'out':
                pg = QWebEnginePage(self.profile())
                def _on_url_changed(u):
                    try:
                        QDesktopServices.openUrl(u)
                    finally:
                        pg.deleteLater()
                pg.urlChanged.connect(_on_url_changed)
                return pg
            else:
                pg = QWebEnginePage(self.profile())
                def _on_url_changed(u):
                    try:
                        self.load(u)
                    finally:
                        pg.deleteLater()
                pg.urlChanged.connect(_on_url_changed)
                return pg
        return super().createWindow(type)

 

class GridContainer(QWidget):
    def __init__(self, mw):
        super().__init__(mw)
        self.mw = mw
    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#1f1f1f'))
        p.setPen(QColor(40,40,40))
        w = getattr(self.mw, 'cellW', 0)
        h = getattr(self.mw, 'cellH', 0)
        s = getattr(self.mw, 'gridSpacing', 0)
        if w <= 0 or h <= 0:
            return
        x = 0
        while x <= self.width():
            p.drawLine(x, 0, x, self.height())
            x += w + s
        y = 0
        while y <= self.height():
            p.drawLine(0, y, self.width(), y)
            y += h + s

class CardWidget(QFrame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setStyleSheet("QFrame{border:2px solid #1554F6;border-radius:10px;background:#1f1f1f;} QLabel.title{color:#fff;padding:2px 8px;border-radius:6px;background:#1677ff;}")
        self.setMinimumSize(260, 220)
        self.config = config.copy()
        self.home = self.config.get('home') or self.config.get('url') or ''
        self.current = self.config.get('url') or self.home
        self.presetMode = self.config.get('mode') or 'in'
        self.mode = 'in'
        self.collapsed = bool(self.config.get('collapsed', False))
        self.title = self.config.get('title') or ''
        self.titleColor = self.config.get('titleColor') or '#1677ff'
        self.zoom = float(self.config.get('zoom', 1.0))
        self.scroll = self.config.get('scroll') or 'hide'
        self.gridW = self.config.get('w') if isinstance(self.config.get('w'), int) and self.config.get('w') > 0 else 1
        self.gridH = self.config.get('h') if isinstance(self.config.get('h'), int) and self.config.get('h') > 0 else 1
        v = QVBoxLayout(self)
        v.setContentsMargins(8,8,8,8)
        v.setSpacing(6)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        self.titleLabel = QLabel(self)
        self.titleLabel.setProperty('class', 'title')
        self.titleLabel.setText(self.default_title())
        self.titleLabel.setStyleSheet(f"QLabel.title{{background:{self.titleColor};}}")
        self.editBtn = QPushButton('修改', self)
        self.toggleBtn = QPushButton('收起' if not self.collapsed else '展开', self)
        self.backBtn = QPushButton('后退', self)
        self.fwdBtn = QPushButton('前进', self)
        self.homeBtn = QPushButton('主页', self)
        self.closeBtn = QPushButton('删除', self)
        self.closeBtn.setStyleSheet("QPushButton{background:#ff4d4f;color:#fff;border:0;border-radius:6px;padding:6px 10px}")
        for w in [self.titleLabel, self.editBtn, self.toggleBtn, self.backBtn, self.fwdBtn, self.homeBtn, self.closeBtn]:
            if isinstance(w, QLabel):
                bar.addWidget(w, 1)
            else:
                bar.addWidget(w)
        v.addLayout(bar)
        self.inputs = QHBoxLayout()
        self.inputs.setSpacing(6)
        self.urlEdit = QLineEdit(self)
        self.urlEdit.setText(self.current)
        self.goBtn = QPushButton('跳转', self)
        self.modeSel = QComboBox(self)
        self.modeSel.addItems(['组件内','外部浏览器'])
        self.modeSel.setCurrentIndex(0)
        self.scrollSel = QComboBox(self)
        self.scrollSel.addItems(['显示滚动条','隐藏滚动条'])
        self.scrollSel.setCurrentIndex(1 if self.scroll=='hide' else 0)
        self.zoomSel = QSlider(Qt.Horizontal, self)
        self.zoomSel.setMinimum(50)
        self.zoomSel.setMaximum(200)
        self.zoomSel.setSingleStep(5)
        self.zoomSel.setValue(int(self.zoom*100))
        self.zoomLabel = QLabel(f"{int(self.zoom*100)}%", self)
        self.colorBtn = QPushButton('标题颜色', self)
        self.titleEdit = QLineEdit(self)
        self.titleEdit.setPlaceholderText('标题')
        self.titleEdit.setText(self.titleLabel.text())
        self.inputs.addWidget(self.urlEdit, 3)
        self.inputs.addWidget(self.goBtn)
        self.inputs.addWidget(self.modeSel)
        self.inputs.addWidget(self.scrollSel)
        self.inputs.addWidget(self.zoomSel, 2)
        self.inputs.addWidget(self.zoomLabel)
        self.inputs.addWidget(self.colorBtn)
        self.inputs.addWidget(self.titleEdit, 2)
        v.addLayout(self.inputs)
        bodyWrap = QVBoxLayout()
        bodyWrap.setContentsMargins(0,0,0,0)
        bodyWrap.setSpacing(0)
        self.web = QWebEngineView(self)
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw and hasattr(mw, 'webProfile'):
            self.web.setPage(Page(mw.webProfile, self))
        else:
            self.web.setPage(Page(self))
        try:
            s = self.web.settings()
            s.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
            s.setAttribute(QWebEngineSettings.PluginsEnabled, True)
            s.setAttribute(QWebEngineSettings.WebGLEnabled, True)
            s.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
            s.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
            self.web.page().fullScreenRequested.connect(lambda r: r.accept())
        except Exception:
            pass
        self.web.installEventFilter(self)
        bodyWrap.addWidget(self.web)
        v.addLayout(bodyWrap)
        self.applyRewrite = (self.presetMode == 'in')
        self.initializingLoad = True
        self.web.loadFinished.connect(self.on_initial_loaded)
        self.apply_collapsed()
        self.apply_zoom(self.zoom)
        self.navigate(self.current, push=False)
        self.editing = False
        self.inputs.setEnabled(False)
        self.editBtn.clicked.connect(self.toggle_edit)
        self.toggleBtn.clicked.connect(self.toggle_collapse)
        self.backBtn.clicked.connect(self.web.back)
        self.fwdBtn.clicked.connect(self.web.forward)
        self.homeBtn.clicked.connect(self.on_home)
        self.closeBtn.clicked.connect(self.on_close)
        self.goBtn.clicked.connect(lambda: self.on_go())
        self.urlEdit.returnPressed.connect(lambda: self.on_go())
        self.modeSel.currentIndexChanged.connect(lambda _: self.on_mode())
        self.scrollSel.currentIndexChanged.connect(lambda _: self.on_scroll())
        self.zoomSel.valueChanged.connect(self.on_zoom)
        self.colorBtn.clicked.connect(self.on_color)
        self.gridRow = config.get('r') if isinstance(config.get('r'), int) else None
        self.gridCol = config.get('c') if isinstance(config.get('c'), int) else None
        self.dragging = False
        self.dragStart = None
        self.resizing = False
        self.resizeHandle = None
        self.resizeStart = None
        self.startW = 0
        self.startH = 0
        self.setMouseTracking(True)

    def on_close(self):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.remove_item(self)

    def default_title(self):
        if self.title:
            return self.title
        try:
            return QUrl(self.current).host() or self.current
        except Exception:
            return self.current

    def toggle_edit(self):
        self.editing = not self.editing
        self.inputs.setEnabled(self.editing)
        self.editBtn.setText('完成' if self.editing else '修改')
        if not self.editing:
            t = self.urlEdit.text().strip()
            if t:
                self.current = t
            tt = self.titleEdit.text().strip()
            if tt:
                self.title = tt
                self.titleLabel.setText(self.title)
        self.save_to_parent()

    def set_editing(self, enabled: bool):
        self.editing = bool(enabled)
        self.inputs.setEnabled(self.editing)
        self.editBtn.setText('完成' if self.editing else '修改')

    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        self.toggleBtn.setText('展开' if self.collapsed else '收起')
        self.apply_collapsed()
        self.save_to_parent()

    def apply_collapsed(self):
        self.web.setVisible(not self.collapsed)

    def on_mode(self):
        self.mode = 'in' if self.modeSel.currentIndex()==0 else 'out'
        self.applyRewrite = (self.mode == 'in')
        self.save_to_parent()

    def on_scroll(self):
        self.scroll = 'hide' if self.scrollSel.currentIndex()==1 else 'show'
        self.inject_scripts()
        self.save_to_parent()

    def on_zoom(self):
        self.zoom = float(self.zoomSel.value())/100.0
        self.zoomLabel.setText(f"{int(self.zoom*100)}%")
        self.apply_zoom(self.zoom)
        self.save_to_parent()

    def on_color(self):
        c = QColorDialog.getColor(QColor(self.titleColor), self)
        if c.isValid():
            self.titleColor = c.name()
            self.titleLabel.setStyleSheet(f"QLabel.title{{background:{self.titleColor};}}")
            self.save_to_parent()

    def on_home(self):
        if not self.home:
            return
        q = QUrl.fromUserInput(self.home)
        if self.mode == 'out':
            QDesktopServices.openUrl(q)
        else:
            self.navigate(self.home, push=True)

    def apply_zoom(self, z):
        self.web.setZoomFactor(z)

    def on_go(self):
        u = self.urlEdit.text().strip()
        if not u:
            return
        q = QUrl.fromUserInput(u)
        if self.mode == 'out':
            QDesktopServices.openUrl(q)
        else:
            self.navigate(u, push=True)

    def navigate(self, url, push=True):
        self.current = url
        self.titleLabel.setText(self.default_title())
        self.web.load(QUrl.fromUserInput(url))
        self.inject_scripts()
        if push:
            self.save_to_parent()

    def inject_scripts(self):
        hide_css = "html,body{overflow:hidden!important;} ::-webkit-scrollbar{width:0!important;height:0!important;display:none!important;}"
        compat_js = """
        (function(){try{
          window.chrome = window.chrome || { runtime: {} };
          try{Object.defineProperty(navigator,'vendor',{get:function(){return 'Google Inc.'}});}catch(e){}
          try{Object.defineProperty(navigator,'platform',{get:function(){return 'Win32'}});}catch(e){}
          try{Object.defineProperty(navigator,'language',{get:function(){return 'zh-CN'}});}catch(e){}
          try{Object.defineProperty(navigator,'languages',{get:function(){return ['zh-CN','zh','en']}});}catch(e){}
          try{Object.defineProperty(navigator,'webdriver',{get:function(){return false}});}catch(e){}
        }catch(e){}})();
        """
        in_js = """
        (function(){try{
          document.querySelectorAll('a[target=\"_blank\"]').forEach(function(a){a.setAttribute('target','_self');});
          window.open = function(u){location.href=u;};
          document.addEventListener('click',function(e){var a=e.target.closest('a[href]'); if(a){a.setAttribute('target','_self');}});
        }catch(e){}})();
        """
        if self.scroll == 'hide':
            css_js = f"(function(){{try{{var s=document.getElementById('__hide_scroll__');if(!s){{s=document.createElement('style');s.id='__hide_scroll__';s.textContent='{hide_css}';document.head.appendChild(s);}}}}catch(e){{}}}})();"
            self.web.page().runJavaScript(css_js)
        self.web.page().runJavaScript(compat_js)
        if getattr(self, 'applyRewrite', False):
            self.web.page().runJavaScript(in_js)

    def on_initial_loaded(self, ok):
        if getattr(self, 'initializingLoad', False):
            self.initializingLoad = False
            self.mode = self.presetMode
            try:
                self.modeSel.setCurrentIndex(0 if self.mode=='in' else 1)
            except Exception:
                pass
            self.applyRewrite = (self.mode == 'in')
            self.save_to_parent()

    def to_dict(self):
        return {
            'type': 'card',
            'url': self.current,
            'home': self.home,
            'mode': self.mode,
            'collapsed': self.collapsed,
            'title': self.titleLabel.text(),
            'titleColor': self.titleColor,
            'zoom': self.zoom,
            'scroll': self.scroll,
            'r': self.gridRow if self.gridRow is not None else -1,
            'c': self.gridCol if self.gridCol is not None else -1,
            'w': self.gridW,
            'h': self.gridH
        }

    def save_to_parent(self):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.save_layout()

    def toggle_detail(self):
        try:
            self.logView.setVisible(not self.logView.isVisible())
        except Exception:
            pass

    def append_log(self, msg: str):
        try:
            ts = time.strftime('%H:%M:%S')
            line = f"[{ts}] {msg}"
            self.logView.appendPlainText(line)
            try:
                self.logView.verticalScrollBar().setValue(self.logView.verticalScrollBar().maximum())
            except Exception:
                pass
            try:
                print(line)
            except Exception:
                pass
        except Exception:
            pass

    def toggle_detail(self):
        try:
            self.logView.setVisible(not self.logView.isVisible())
        except Exception:
            pass

    def append_log(self, msg: str):
        try:
            ts = time.strftime('%H:%M:%S')
            line = f"[{ts}] {msg}"
            self.logView.appendPlainText(line)
            try:
                self.logView.verticalScrollBar().setValue(self.logView.verticalScrollBar().maximum())
            except Exception:
                pass
            try:
                print(line)
            except Exception:
                pass
        except Exception:
            pass

    def toggle_detail(self):
        try:
            self.logView.setVisible(not self.logView.isVisible())
        except Exception:
            pass

    def append_log(self, msg: str):
        try:
            ts = time.strftime('%H:%M:%S')
            line = f"[{ts}] {msg}"
            self.logView.appendPlainText(line)
            try:
                self.logView.verticalScrollBar().setValue(self.logView.verticalScrollBar().maximum())
            except Exception:
                pass
            try:
                print(line)
            except Exception:
                pass
        except Exception:
            pass
    def toggle_detail(self):
        try:
            self.logView.setVisible(not self.logView.isVisible())
        except Exception:
            pass
    def append_log(self, msg: str):
        try:
            ts = time.strftime('%H:%M:%S')
            line = f"[{ts}] {msg}"
            self.logView.appendPlainText(line)
            try:
                self.logView.verticalScrollBar().setValue(self.logView.verticalScrollBar().maximum())
            except Exception:
                pass
            try:
                print(line)
            except Exception:
                pass
        except Exception:
            pass
    def mousePressEvent(self, e):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw and mw.locked:
            QFrame.mousePressEvent(self, e)
            return
        if mw:
            mw.activeWeb = self.web
        pos = e.position().toPoint()
        h = self.hitHandle(pos)
        if h:
            self.resizing = True
            self.resizeHandle = h
            self.resizeStart = pos
            self.startW = self.width()
            self.startH = self.height()
        else:
            self.dragging = True
            self.dragStart = pos
            self.raise_()
        QFrame.mousePressEvent(self, e)
    def mouseMoveEvent(self, e):
        if self.resizing:
            mw = self.parent()
            while mw and not isinstance(mw, MainWindow):
                mw = mw.parent()
            if mw:
                mw.compute_metrics()
                pos = e.position().toPoint()
                dx = pos.x() - self.resizeStart.x()
                dy = pos.y() - self.resizeStart.y()
                newW = self.startW
                newH = self.startH
                if self.resizeHandle in ('right','corner'):
                    newW = max(100, self.startW + dx)
                if self.resizeHandle in ('bottom','corner'):
                    newH = max(120, self.startH + dy)
                cellW = mw.cellW
                cellH = mw.cellH
                s = mw.gridSpacing
                gw = max(1, int(round((newW + s) / (cellW + s))))
                gh = max(1, int(round((newH + s) / (cellH + s))))
                while gw > 0 and (self.gridCol or 0) + gw > mw.gridCols:
                    gw -= 1
                if gw < 1:
                    gw = 1
                while mw.is_occupied_except(self, self.gridRow or 0, self.gridCol or 0, gw, gh):
                    if gw > 1:
                        gw -= 1
                    elif gh > 1:
                        gh -= 1
                    else:
                        break
                self.gridW = gw
                self.gridH = gh
                mw.place_card(self)
            QFrame.mouseMoveEvent(self, e)
            return
        if not self.dragging:
            pos = e.position().toPoint()
            h = self.hitHandle(pos)
            if h == 'right':
                self.setCursor(Qt.SizeHorCursor)
            elif h == 'bottom':
                self.setCursor(Qt.SizeVerCursor)
            elif h == 'corner':
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            QFrame.mouseMoveEvent(self, e)
            return
        pos = e.position().toPoint()
        dx = pos.x() - self.dragStart.x()
        dy = pos.y() - self.dragStart.y()
        self.move(self.x() + dx, self.y() + dy)
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.preview_snap(self)
        QFrame.mouseMoveEvent(self, e)
    def mouseReleaseEvent(self, e):
        if self.resizing:
            self.resizing = False
            mw = self.parent()
            while mw and not isinstance(mw, MainWindow):
                mw = mw.parent()
            if mw:
                mw.save_layout()
            QFrame.mouseReleaseEvent(self, e)
            return
        self.dragging = False
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.finish_snap(self)
        QFrame.mouseReleaseEvent(self, e)
    def hitHandle(self, pos):
        r = 8
        onRight = pos.x() >= self.width() - r
        onBottom = pos.y() >= self.height() - r
        if onRight and onBottom:
            return 'corner'
        if onRight:
            return 'right'
        if onBottom:
            return 'bottom'
        return None

    def eventFilter(self, obj, ev):
        if obj is self.web:
            if ev.type() == QEvent.MouseButtonPress:
                mw = self.parent()
                while mw and not isinstance(mw, MainWindow):
                    mw = mw.parent()
                if mw:
                    mw.activeWeb = self.web
                try:
                    if not self.web.hasFocus():
                        self.web.setFocus()
                except Exception:
                    pass
                return False
            if ev.type() == QEvent.Wheel:
                mw = self.parent()
                while mw and not isinstance(mw, MainWindow):
                    mw = mw.parent()
                if mw and getattr(mw, 'activeWeb', None) is self.web:
                    try:
                        if not self.web.hasFocus():
                            self.web.setFocus()
                    except Exception:
                        pass
                    return False
                return True
        return QFrame.eventFilter(self, obj, ev)

    

class SpacerWidget(QFrame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setStyleSheet("QFrame{border:2px solid #1554F6;border-radius:10px;background:#1f1f1f;}")
        self.setMinimumSize(60, 60)
        self.gridW = config.get('w') if isinstance(config.get('w'), int) and config.get('w') > 0 else 1
        self.gridH = config.get('h') if isinstance(config.get('h'), int) and config.get('h') > 0 else 1
        v = QVBoxLayout(self)
        v.setContentsMargins(8,8,8,8)
        v.setSpacing(6)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        self.titleLabel = QLabel('格子', self)
        self.closeBtn = QPushButton('删除', self)
        self.closeBtn.setStyleSheet("QPushButton{background:#ff4d4f;color:#fff;border:0;border-radius:6px;padding:6px 10px}")
        bar.addWidget(self.titleLabel, 1)
        bar.addWidget(self.closeBtn)
        v.addLayout(bar)
        self.gridRow = config.get('r') if isinstance(config.get('r'), int) else None
        self.gridCol = config.get('c') if isinstance(config.get('c'), int) else None
        self.dragging = False
        self.dragStart = None
        self.resizing = False
        self.resizeHandle = None
        self.resizeStart = None
        self.startW = 0
        self.startH = 0
        self.setMouseTracking(True)
        self.closeBtn.clicked.connect(self.on_close)
    def to_dict(self):
        return {
            'type': 'spacer',
            'r': self.gridRow if self.gridRow is not None else -1,
            'c': self.gridCol if self.gridCol is not None else -1,
            'w': self.gridW,
            'h': self.gridH
        }
    def save_to_parent(self):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.save_layout()
    def on_close(self):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.remove_item(self)
    def hitHandle(self, pos):
        r = 8
        onRight = pos.x() >= self.width() - r
        onBottom = pos.y() >= self.height() - r
        if onRight and onBottom:
            return 'corner'
        if onRight:
            return 'right'
        if onBottom:
            return 'bottom'
        return None
    def mousePressEvent(self, e):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw and mw.locked:
            QFrame.mousePressEvent(self, e)
            return
        pos = e.position().toPoint()
        h = self.hitHandle(pos)
        if h:
            self.resizing = True
            self.resizeHandle = h
            self.resizeStart = pos
            self.startW = self.width()
            self.startH = self.height()
        else:
            self.dragging = True
            self.dragStart = pos
            self.raise_()
        QFrame.mousePressEvent(self, e)
    def mouseMoveEvent(self, e):
        if self.resizing:
            mw = self.parent()
            while mw and not isinstance(mw, MainWindow):
                mw = mw.parent()
            if mw:
                mw.compute_metrics()
                pos = e.position().toPoint()
                dx = pos.x() - self.resizeStart.x()
                dy = pos.y() - self.resizeStart.y()
                newW = self.startW
                newH = self.startH
                if self.resizeHandle in ('right','corner'):
                    newW = max(60, self.startW + dx)
                if self.resizeHandle in ('bottom','corner'):
                    newH = max(60, self.startH + dy)
                cellW = mw.cellW
                cellH = mw.cellH
                s = mw.gridSpacing
                gw = max(1, int(round((newW + s) / (cellW + s))))
                gh = max(1, int(round((newH + s) / (cellH + s))))
                while gw > 0 and (self.gridCol or 0) + gw > mw.gridCols:
                    gw -= 1
                if gw < 1:
                    gw = 1
                while mw.is_occupied_except(self, self.gridRow or 0, self.gridCol or 0, gw, gh):
                    if gw > 1:
                        gw -= 1
                    elif gh > 1:
                        gh -= 1
                    else:
                        break
                self.gridW = gw
                self.gridH = gh
                mw.place_card(self)
            QFrame.mouseMoveEvent(self, e)
            return
        if not self.dragging:
            pos = e.position().toPoint()
            h = self.hitHandle(pos)
            if h == 'right':
                self.setCursor(Qt.SizeHorCursor)
            elif h == 'bottom':
                self.setCursor(Qt.SizeVerCursor)
            elif h == 'corner':
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            QFrame.mouseMoveEvent(self, e)
            return
        pos = e.position().toPoint()
        dx = pos.x() - self.dragStart.x()
        dy = pos.y() - self.dragStart.y()
        self.move(self.x() + dx, self.y() + dy)
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.preview_snap(self)
        QFrame.mouseMoveEvent(self, e)
    def mouseReleaseEvent(self, e):
        if self.resizing:
            self.resizing = False
            mw = self.parent()
            while mw and not isinstance(mw, MainWindow):
                mw = mw.parent()
            if mw:
                mw.save_layout()
            QFrame.mouseReleaseEvent(self, e)
            return
        self.dragging = False
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.finish_snap(self)
        QFrame.mouseReleaseEvent(self, e)
        

class DesktopAppWidget(QFrame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setStyleSheet("QFrame{border:2px solid #1554F6;border-radius:10px;background:#1f1f1f;} QLabel.title{color:#fff;padding:2px 8px;border-radius:6px;background:#1677ff;}")
        self.setMinimumSize(260, 220)
        self.config = config.copy()
        self.title = self.config.get('title') or '桌面'
        self.titleColor = self.config.get('titleColor') or '#1677ff'
        self.collapsed = bool(self.config.get('collapsed', False))
        
        self.match = (self.config.get('match') or '').strip()
        self.regex = bool(self.config.get('regex', False))
        self.classMatch = (self.config.get('classMatch') or '').strip()
        self.classRegex = bool(self.config.get('classRegex', False))
        self.lastTitle = (self.config.get('lastTitle') or '').strip()
        self.lastClass = (self.config.get('lastClass') or '').strip()
        self.lastBounds = self.config.get('lastBounds') if isinstance(self.config.get('lastBounds'), dict) else {}
        self.selLabel = (self.config.get('selLabel') or '').strip()
        self.gridW = self.config.get('w') if isinstance(self.config.get('w'), int) and self.config.get('w') > 0 else 1
        self.gridH = self.config.get('h') if isinstance(self.config.get('h'), int) and self.config.get('h') > 0 else 1
        self.target_hwnd = int(self.config.get('hwnd') or 0) if isinstance(self.config.get('hwnd'), int) else 0
        v = QVBoxLayout(self)
        v.setContentsMargins(8,8,8,8)
        v.setSpacing(6)
        bar = QHBoxLayout()
        bar.setSpacing(6)
        self.titleLabel = QLabel(self)
        self.titleLabel.setProperty('class', 'title')
        self.titleLabel.setText(self.title)
        self.titleLabel.setStyleSheet(f"QLabel.title{{background:{self.titleColor};}}")
        self.editBtn = QPushButton('修改', self)
        self.toggleBtn = QPushButton('收起' if not self.collapsed else '展开', self)
        self.exitBtn = QPushButton('重载', self)
        self.detailBtn = QPushButton('详情', self)
        self.closeBtn = QPushButton('删除', self)
        self.closeBtn.setStyleSheet("QPushButton{background:#ff4d4f;color:#fff;border:0;border-radius:6px;padding:6px 10px}")
        bar.addWidget(self.titleLabel, 1)
        bar.addWidget(self.editBtn)
        bar.addWidget(self.toggleBtn)
        bar.addWidget(self.exitBtn)
        bar.addWidget(self.detailBtn)
        bar.addWidget(self.closeBtn)
        v.addLayout(bar)
        self.inputs = QHBoxLayout()
        self.inputs.setSpacing(6)
        self.windowSel = QComboBox(self)
        self.matchEdit = QLineEdit(self)
        self.matchEdit.setPlaceholderText('窗口标题包含/正则')
        if self.match:
            self.matchEdit.setText(self.match)
        self.regexChk = QCheckBox('正则', self)
        self.regexChk.setChecked(self.regex)
        self.classEdit = QLineEdit(self)
        self.classEdit.setPlaceholderText('窗口类名包含/正则')
        if self.classMatch:
            self.classEdit.setText(self.classMatch)
        self.classRegexChk = QCheckBox('正则', self)
        self.classRegexChk.setChecked(self.classRegex)
        self.refreshBtn = QPushButton('刷新', self)
        
        self.fitBtn = QPushButton('自适应', self)
        self.colorBtn = QPushButton('标题颜色', self)
        self.titleEdit = QLineEdit(self)
        self.titleEdit.setPlaceholderText('标题')
        self.titleEdit.setText(self.titleLabel.text())
        self.inputs.addWidget(self.matchEdit, 2)
        self.inputs.addWidget(self.regexChk)
        self.inputs.addWidget(self.classEdit, 2)
        self.inputs.addWidget(self.classRegexChk)
        self.inputs.addWidget(self.windowSel, 3)
        self.inputs.addWidget(self.refreshBtn)
        
        self.inputs.addWidget(self.fitBtn)
        self.inputs.addWidget(self.colorBtn)
        self.inputs.addWidget(self.titleEdit, 2)
        v.addLayout(self.inputs)
        bodyWrap = QVBoxLayout()
        bodyWrap.setContentsMargins(0,0,0,0)
        bodyWrap.setSpacing(0)
        self.host = QWidget(self)
        try:
            self.host.setAttribute(Qt.WA_NativeWindow, True)
        except Exception:
            pass
        bodyWrap.addWidget(self.host)
        self.logView = QPlainTextEdit(self)
        try:
            self.logView.setReadOnly(True)
            self.logView.setMaximumBlockCount(500)
            self.logView.setVisible(False)
            self.logView.setFixedHeight(140)
        except Exception:
            pass
        bodyWrap.addWidget(self.logView)
        v.addLayout(bodyWrap)
        self.apply_collapsed()
        self.editing = False
        self.inputs.setEnabled(False)
        self.editBtn.clicked.connect(self.toggle_edit)
        self.toggleBtn.clicked.connect(self.toggle_collapse)
        self.exitBtn.clicked.connect(self.on_reload)
        self.detailBtn.clicked.connect(self.toggle_detail)
        self.closeBtn.clicked.connect(self.on_close)
        self.refreshBtn.clicked.connect(self.on_refresh)
        self.windowSel.currentIndexChanged.connect(lambda _: self.on_select_window())
        self.matchEdit.returnPressed.connect(self.on_match_changed)
        self.regexChk.stateChanged.connect(lambda _: self.on_match_changed())
        self.classEdit.returnPressed.connect(self.on_class_changed)
        self.classRegexChk.stateChanged.connect(lambda _: self.on_class_changed())
        
        self.fitBtn.clicked.connect(self.on_fit)
        self.colorBtn.clicked.connect(self.on_color)
        self.gridRow = config.get('r') if isinstance(config.get('r'), int) else None
        self.gridCol = config.get('c') if isinstance(config.get('c'), int) else None
        self.dragging = False
        self.dragStart = None
        self.resizing = False
        self.resizeHandle = None
        self.resizeStart = None
        self.startW = 0
        self.startH = 0
        self.setMouseTracking(True)
        self.refresh_windows()
        if self.target_hwnd:
            self.embed_window(self.target_hwnd)
        else:
            try:
                self.try_auto_bind()
            except Exception:
                pass
            try:
                self.ensure_monitor_started()
            except Exception:
                pass
            try:
                self._monitor_tick()
            except Exception:
                pass
    def on_fit(self):
        self.resize_target_window()
        try:
            host_hwnd = int(self.host.winId())
            try:
                l, tt, r, b = win32gui.GetClientRect(host_hwnd)
                self.lastBounds = {'w': int(r - l), 'h': int(b - tt)}
            except Exception:
                rr = self.host.rect()
                self.lastBounds = {'w': int(rr.width()), 'h': int(rr.height())}
        except Exception:
            pass
        self.save_to_parent()
    def toggle_edit(self):
        self.editing = not self.editing
        self.inputs.setEnabled(self.editing)
        self.editBtn.setText('完成' if self.editing else '修改')
        if not self.editing:
            tt = self.titleEdit.text().strip()
            if tt:
                self.title = tt
                self.titleLabel.setText(self.title)
            self.match = self.matchEdit.text().strip()
            self.regex = bool(self.regexChk.isChecked())
            self.classMatch = self.classEdit.text().strip()
            self.classRegex = bool(self.classRegexChk.isChecked())
            self.refresh_windows()
            self.try_auto_bind()
        self.save_to_parent()

    def set_editing(self, enabled: bool):
        self.editing = bool(enabled)
        self.inputs.setEnabled(self.editing)
        self.editBtn.setText('完成' if self.editing else '修改')

    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        self.toggleBtn.setText('展开' if self.collapsed else '收起')
        self.apply_collapsed()
        self.save_to_parent()

    def apply_collapsed(self):
        self.host.setVisible(not self.collapsed)

    

    def on_color(self):
        c = QColorDialog.getColor(QColor(self.titleColor), self)
        if c.isValid():
            self.titleColor = c.name()
            self.titleLabel.setStyleSheet(f"QLabel.title{{background:{self.titleColor};}}")
            self.save_to_parent()

    def on_refresh(self):
        try:
            self.refresh_windows()
        except Exception:
            pass
        try:
            self.try_auto_bind()
        except Exception:
            pass
        try:
            self.ensure_monitor_started()
        except Exception:
            pass
        try:
            self._monitor_tick()
        except Exception:
            pass

    def _is_system_window(self, hwnd, cls, title):
        try:
            if hwnd == win32gui.GetDesktopWindow():
                return True
        except Exception:
            pass
        c = (cls or '').lower()
        t = (title or '').lower()
        bl = {
            'progman',
            'workerw',
            'shell_traywnd',
            'shell_secondarytraywnd',
            'traynotifywnd',
            'toplevelwindowforoverflow',
            'multitaskingviewframe',
            'windows.ui.core.corewindow'
        }
        if c in bl:
            return True
        if t in ('program manager',):
            return True
        return False

    def _normalize_title(self, s: str) -> str:
        try:
            t = (s or '').strip()
            import re
            # strip trailing parentheses segments, both English () and Chinese （）
            t = re.sub(r"\s*[（(].*?[）)]\s*$", "", t)
            return t.strip()
        except Exception:
            return (s or '').strip()

    def refresh_windows(self):
        self.windowSel.blockSignals(True)
        self.windowSel.clear()
        if win32gui is None:
            self.windowSel.addItem('未安装pywin32')
            self.windowSel.setEnabled(False)
            self.windowSel.blockSignals(False)
            return
        items = []
        def _cb(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd)
                try:
                    cls = win32gui.GetClassName(hwnd)
                except Exception:
                    cls = ''
                if t:
                    items.append((hwnd, t, cls))
            return True
        try:
            win32gui.EnumWindows(_cb, None)
        except Exception:
            items = []
        title_pat = (self.match or '').strip()
        class_pat = (self.classMatch or '').strip()
        filtered = []
        for hwnd, t, cls in items:
            ok_title = True
            ok_class = True
            if title_pat:
                if self.regex:
                    try:
                        ok_title = bool(__import__('re').search(title_pat, self._normalize_title(t)))
                    except Exception:
                        ok_title = title_pat.lower() in self._normalize_title(t).lower()
                else:
                    ok_title = title_pat.lower() in self._normalize_title(t).lower()
            if class_pat:
                if self.classRegex:
                    try:
                        ok_class = bool(__import__('re').search(class_pat, cls))
                    except Exception:
                        ok_class = class_pat.lower() in (cls or '').lower()
                else:
                    ok_class = class_pat.lower() in (cls or '').lower()
            if ok_title and ok_class:
                filtered.append((hwnd, t, cls))
        safe_items = []
        risky_items = []
        for hwnd, t, cls in filtered:
            if self._is_system_window(hwnd, cls, t):
                risky_items.append((hwnd, t, cls))
            else:
                safe_items.append((hwnd, t, cls))
        try:
            self.append_log(f"候选总数: {len(items)} | 筛选后: {len(filtered)} | 无风险: {len(safe_items)} | 有风险: {len(risky_items)}")
        except Exception:
            pass
        self.windowSel.addItem("—— 无风险项 ——", None)
        for hwnd, t, cls in safe_items:
            self.windowSel.addItem(f"{t} ({cls})", hwnd)
        self.windowSel.addItem("—— 有风险项 ——", None)
        for hwnd, t, cls in risky_items:
            self.windowSel.addItem(f"[风险] {t} ({cls})", hwnd)
        self.windowSel.blockSignals(False)
        try:
            if not self.target_hwnd:
                self.ensure_monitor_started()
        except Exception:
            pass
        if self.target_hwnd:
            idx = -1
            for i in range(self.windowSel.count()):
                if int(self.windowSel.itemData(i) or 0) == int(self.target_hwnd):
                    idx = i
                    break
            if idx >= 0:
                self.windowSel.setCurrentIndex(idx)
        elif (self.selLabel or '').strip():
            try:
                want = (self.selLabel or '').strip().lower()
                idx = -1
                for i in range(self.windowSel.count()):
                    txt = (self.windowSel.itemText(i) or '').strip()
                    if txt.startswith('[风险] '):
                        txt = txt[4:].strip()
                    if txt and want and txt.lower() == want:
                        idx = i
                        break
                if idx >= 0:
                    self.windowSel.blockSignals(True)
                    self.windowSel.setCurrentIndex(idx)
                self.windowSel.blockSignals(False)
            except Exception:
                pass
        elif self.windowSel.count() > 0:
            try:
                self.windowSel.blockSignals(True)
                sel = 0
                for i in range(self.windowSel.count()):
                    d = self.windowSel.itemData(i)
                    txt = (self.windowSel.itemText(i) or '').strip()
                    if isinstance(d, int) and d:
                        sel = i
                        break
                    if txt and not txt.startswith('——') and txt != '未安装pywin32':
                        sel = i
                        break
                self.windowSel.setCurrentIndex(sel)
                try:
                    lab = (self.windowSel.itemText(sel) or '').strip()
                    if lab.startswith('[风险] '):
                        lab = lab[4:].strip()
                    self.selLabel = lab
                    try:
                        tname = lab
                        if ' (' in tname:
                            try:
                                tname = tname.rsplit(' (', 1)[0]
                            except Exception:
                                pass
                        try:
                            tname = self._normalize_title(tname)
                        except Exception:
                            pass
                        self.titleEdit.setText(tname)
                    except Exception:
                        pass
                except Exception:
                    pass
            finally:
                self.windowSel.blockSignals(False)

    def on_select_window(self):
        txt = self.windowSel.currentText()
        title = (txt or '').strip()
        if title.startswith('[风险] '):
            title = title[4:].strip()
        if ' (' in title:
            try:
                title = title.rsplit(' (', 1)[0]
            except Exception:
                pass
        try:
            title = self._normalize_title(title)
        except Exception:
            pass
        try:
            lab = (self.windowSel.currentText() or '').strip()
            if lab.startswith('[风险] '):
                lab = lab[4:].strip()
            self.selLabel = lab
        except Exception:
            pass
        target = 0
        if win32gui:
            items = []
            def _cb(h, extra):
                t = win32gui.GetWindowText(h)
                if t:
                    items.append((h, t))
                return True
            try:
                win32gui.EnumWindows(_cb, None)
            except Exception:
                items = []
            best = None
            score = 0.0
            tl = (title or '').lower()
            for h, t in items:
                tt = self._normalize_title(t or '').lower()
                s = 0.0
                if tl and tl in tt:
                    s = max(s, 1.0)
                if tl and tt:
                    try:
                        s = max(s, difflib.SequenceMatcher(a=tl, b=tt).ratio())
                    except Exception:
                        pass
                if s > score:
                    score = s
                    best = h
            if best and score >= 0.6:
                target = int(best)
        if target:
            self.embed_window(target)
            self.lastTitle = title or self.lastTitle
            self.save_to_parent()
            try:
                if getattr(self, 'monitorTimer', None):
                    self.monitorTimer.stop()
            except Exception:
                pass
        else:
            self.ensure_monitor_started()

    def on_match_changed(self):
        self.match = self.matchEdit.text().strip()
        self.regex = bool(self.regexChk.isChecked())
        self.refresh_windows()
        self.try_auto_bind()
        self.save_to_parent()
        try:
            if not self.target_hwnd:
                self.ensure_monitor_started()
        except Exception:
            pass

    def on_class_changed(self):
        self.classMatch = self.classEdit.text().strip()
        self.classRegex = bool(self.classRegexChk.isChecked())
        self.refresh_windows()
        self.try_auto_bind()
        self.save_to_parent()
        try:
            if not self.target_hwnd:
                self.ensure_monitor_started()
        except Exception:
            pass

    def try_auto_bind(self):
        if self.target_hwnd:
            return
        self.append_log('自动置入尝试开始')
        hwnd = 0
        if win32gui:
            items = []
            def _cb(h, extra):
                t = win32gui.GetWindowText(h)
                try:
                    cls = win32gui.GetClassName(h)
                except Exception:
                    cls = ''
                if t:
                    items.append((h, t, cls))
                return True
            try:
                win32gui.EnumWindows(_cb, None)
            except Exception:
                items = []
            title_pat = (self.match or '').strip()
            class_pat = (self.classMatch or '').strip()
            filtered = []
            for h, t, cls in items:
                ok_title = True
                ok_class = True
                if title_pat:
                    if self.regex:
                        try:
                            ok_title = bool(__import__('re').search(title_pat, t))
                        except Exception:
                            ok_title = title_pat.lower() in t.lower()
                    else:
                        ok_title = title_pat.lower() in t.lower()
                if class_pat:
                    if self.classRegex:
                        try:
                            ok_class = bool(__import__('re').search(class_pat, cls))
                        except Exception:
                            ok_class = class_pat.lower() in (cls or '').lower()
                    else:
                        ok_class = class_pat.lower() in (cls or '').lower()
                if ok_title and ok_class:
                    filtered.append((h, t, cls))
            best = None
            score = 0.0
            want_label = (self.selLabel or '').strip().lower()
            lt = self._normalize_title(self.lastTitle or '').lower().strip()
            lc = (self.lastClass or '').lower().strip()
            title_pat_l = (title_pat or '').lower()
            class_pat_l = (class_pat or '').lower()
            LTL = lt or title_pat_l
            LCL = lc or class_pat_l
            pool = filtered if filtered else items
            for h, t, cls in pool:
                s = 0.0
                lbl = (f"{(t or '').strip()} ({(cls or '').strip()})" if cls else (t or '').strip()).lower()
                tl = self._normalize_title(t or '').lower()
                cl = (cls or '').lower()
                if want_label and lbl and lbl == want_label:
                    s = max(s, 2.0)
                if LTL and LTL in tl:
                    s = max(s, 1.0)
                if LCL and LCL in cl:
                    s = max(s, 1.0)
                if LTL and tl:
                    try:
                        s = max(s, difflib.SequenceMatcher(a=LTL, b=tl).ratio())
                    except Exception:
                        pass
                if LCL and cl:
                    try:
                        s = max(s, difflib.SequenceMatcher(a=LCL, b=cl).ratio())
                    except Exception:
                        pass
                try:
                    self.append_log(f"候选评分: {lbl} | 标题规范: {tl} | 类: {cl} | 分数: {s:.2f}")
                except Exception:
                    pass
                if s > score:
                    score = s
                    best = (h, t, cls)
            if best and score >= 0.8:
                hwnd = int(best[0])
            try:
                if hwnd:
                    self.append_log(f"选择窗口: {win32gui.GetWindowText(hwnd)} ({win32gui.GetClassName(hwnd)}) | 评分: {score:.2f}")
                else:
                    self.append_log("未找到合格候选，等待监控")
            except Exception:
                pass
        if hwnd:
            self.embed_window(hwnd)
            self.save_to_parent()

    def ensure_monitor_started(self):
        try:
            if not getattr(self, 'monitorTimer', None):
                self.monitorTimer = QTimer(self)
                self.monitorTimer.setInterval(5000)
                self.monitorTimer.timeout.connect(self._monitor_tick)
            if not self.monitorTimer.isActive():
                self.monitorTimer.start()
        except Exception:
            pass
    def _start_aggressive_reload(self):
        try:
            self._aggressiveRemain = 8
            if not getattr(self, 'aggressiveTimer', None):
                self.aggressiveTimer = QTimer(self)
                self.aggressiveTimer.setInterval(1000)
                self.aggressiveTimer.timeout.connect(self._aggressive_tick)
            self.aggressiveTimer.start()
        except Exception:
            pass
    def _aggressive_tick(self):
        try:
            if self.target_hwnd:
                if getattr(self, 'aggressiveTimer', None):
                    self.aggressiveTimer.stop()
                return
            try:
                self.try_auto_bind()
            except Exception:
                pass
            try:
                self._monitor_tick()
            except Exception:
                pass
            try:
                self._aggressiveRemain = int(getattr(self, '_aggressiveRemain', 0)) - 1
            except Exception:
                self._aggressiveRemain = 0
            if self._aggressiveRemain <= 0:
                if getattr(self, 'aggressiveTimer', None):
                    self.aggressiveTimer.stop()
        except Exception:
            try:
                if getattr(self, 'aggressiveTimer', None):
                    self.aggressiveTimer.stop()
            except Exception:
                pass

    def _monitor_tick(self):
        try:
            self.append_log('监控检测触发')
            if self.target_hwnd:
                if getattr(self, 'monitorTimer', None):
                    self.monitorTimer.stop()
                self.append_log('已置入，停止监控')
                return
            lt = self._normalize_title(self.lastTitle or '').strip()
            lc = (self.lastClass or '').strip()
            mp_title = (self.match or '').strip()
            mp_class = (self.classMatch or '').strip()
            if not lt and not lc and not mp_title and not mp_class:
                self.append_log('缺少匹配依据，跳过')
                return
            cand = []
            def _cb(h, extra):
                t = win32gui.GetWindowText(h)
                try:
                    cls = win32gui.GetClassName(h)
                except Exception:
                    cls = ''
                if t:
                    cand.append((h, t, cls))
                return True
            try:
                win32gui.EnumWindows(_cb, None)
            except Exception:
                cand = []
            best = None
            score = 0.0
            want_label = (self.selLabel or '').strip().lower()
            LTL = (self._normalize_title(lt or mp_title)).lower()
            LCL = (lc or mp_class).lower()
            for h, t, cls in cand:
                lbl = (f"{(t or '').strip()} ({(cls or '').strip()})" if cls else (t or '').strip()).lower()
                tl = self._normalize_title(t or '').lower()
                cl = (cls or '').lower()
                s = 0.0
                if want_label and lbl and lbl == want_label:
                    s = max(s, 2.0)
                if LTL and LTL in tl:
                    s = max(s, 1.0)
                if LCL and LCL in cl:
                    s = max(s, 1.0)
                if LTL and tl:
                    try:
                        s = max(s, difflib.SequenceMatcher(a=LTL, b=tl).ratio())
                    except Exception:
                        pass
                if LCL and cl:
                    try:
                        s = max(s, difflib.SequenceMatcher(a=LCL, b=cl).ratio())
                    except Exception:
                        pass
                try:
                    self.append_log(f"监控评分: {lbl} | 标题规范: {tl} | 类: {cl} | 分数: {s:.2f}")
                except Exception:
                    pass
                if s > score:
                    score = s
                    best = (h, t, cls)
            if best and score >= 0.6:
                try:
                    self.embed_window(int(best[0]))
                    self.save_to_parent()
                    if getattr(self, 'monitorTimer', None):
                        self.monitorTimer.stop()
                    try:
                        self.append_log(f"监控选择窗口: {best[1]} ({best[2]}) | 评分: {score:.2f}")
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def embed_window(self, hwnd):
        if win32gui is None:
            return
        try:
            try:
                t0 = win32gui.GetWindowText(hwnd)
            except Exception:
                t0 = ''
            try:
                c0 = win32gui.GetClassName(hwnd)
            except Exception:
                c0 = ''
            try:
                self.append_log(f"准备嵌入: {t0} ({c0})")
            except Exception:
                pass
            if self._is_system_window(hwnd, c0, t0):
                mb = QMessageBox(self)
                mb.setIcon(QMessageBox.Warning)
                mb.setWindowTitle('风险提醒')
                mb.setText('选择的是系统窗口，可能影响系统桌面或任务栏。\n是否继续嵌入？')
                mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                if mb.exec() != QMessageBox.Yes:
                    return
            if self.target_hwnd and int(self.target_hwnd) != int(hwnd):
                try:
                    self.restore_window_state(self.target_hwnd)
                except Exception:
                    pass
            # capture original state BEFORE modifying
            try:
                self.capture_window_state(hwnd)
            except Exception:
                pass
            try:
                if win32gui.IsIconic(hwnd):
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except Exception:
                pass
            host_hwnd = int(self.host.winId())
            win32gui.SetParent(hwnd, host_hwnd)
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style &= ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZEBOX | win32con.WS_MAXIMIZEBOX | win32con.WS_SYSMENU | win32con.WS_POPUP)
            style |= win32con.WS_CHILD
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            try:
                ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                ex &= ~getattr(win32con, 'WS_EX_TOPMOST', 0)
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)
            except Exception:
                pass
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except Exception:
                pass
            try:
                win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED)
            except Exception:
                pass
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            try:
                t = win32gui.GetWindowText(hwnd)
            except Exception:
                t = ''
            try:
                cls = win32gui.GetClassName(hwnd)
            except Exception:
                cls = ''
            self.lastTitle = self._normalize_title(t) or self.lastTitle
            self.lastClass = cls or self.lastClass
            try:
                self.selLabel = f"{(t or '').strip()} ({(cls or '').strip()})" if cls else (t or '').strip()
            except Exception:
                pass
            try:
                host_hwnd = int(self.host.winId())
                l, tt, r, b = win32gui.GetClientRect(host_hwnd)
                self.lastBounds = {'w': int(r - l), 'h': int(b - tt)}
            except Exception:
                pass
            try:
                self.append_log(f"嵌入完成: {t} ({cls}) | 尺寸: {self.lastBounds.get('w','?')}x{self.lastBounds.get('h','?')}")
            except Exception:
                pass
            self.target_hwnd = hwnd
        except Exception:
            pass

    def resize_target_window(self):
        if win32gui is None:
            return
        if not self.target_hwnd:
            return
        try:
            host_hwnd = int(self.host.winId())
            try:
                l, t, r, b = win32gui.GetClientRect(host_hwnd)
                w = max(0, int(r - l))
                h = max(0, int(b - t))
            except Exception:
                rr = self.host.rect()
                w = int(rr.width())
                h = int(rr.height())
            x = 0
            y = 0
            try:
                win32gui.MoveWindow(self.target_hwnd, x, y, w, h, True)
            except Exception:
                pass
            try:
                win32gui.SetWindowPos(self.target_hwnd, 0, x, y, w, h, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
            except Exception:
                pass
        except Exception:
            pass

    def resizeEvent(self, e):
        QFrame.resizeEvent(self, e)

    def to_dict(self):
        return {
            'type': 'desktop',
            'collapsed': self.collapsed,
            'title': self.titleLabel.text(),
            'titleColor': self.titleColor,
            
            'match': self.match,
            'regex': bool(self.regex),
            'classMatch': self.classMatch,
            'classRegex': bool(self.classRegex),
            'lastTitle': self.lastTitle,
            'lastClass': self.lastClass,
            'lastBounds': self.lastBounds,
            'selLabel': self.selLabel,
            'hwnd': int(self.target_hwnd) if self.target_hwnd else 0,
            'r': self.gridRow if self.gridRow is not None else -1,
            'c': self.gridCol if self.gridCol is not None else -1,
            'w': self.gridW,
            'h': self.gridH
        }

    def save_to_parent(self):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.save_layout()
    def toggle_detail(self):
        try:
            self.logView.setVisible(not self.logView.isVisible())
        except Exception:
            pass
    def append_log(self, msg: str):
        try:
            ts = time.strftime('%H:%M:%S')
            line = f"[{ts}] {msg}"
            self.logView.appendPlainText(line)
            try:
                self.logView.verticalScrollBar().setValue(self.logView.verticalScrollBar().maximum())
            except Exception:
                pass
            try:
                print(line)
            except Exception:
                pass
        except Exception:
            pass
    def on_reload(self):
        self.append_log('重载开始')
        try:
            self.refresh_windows()
            self.append_log('候选池已刷新')
        except Exception:
            pass
        try:
            self.try_auto_bind()
            self.append_log('已尝试自动置入（优先依据 selLabel/最后一次记录）')
        except Exception:
            pass
        try:
            self.ensure_monitor_started()
            self.append_log('已启动5s监控')
        except Exception:
            pass
        try:
            self._monitor_tick()
            self.append_log('触发一次监控检查')
        except Exception:
            pass
        try:
            self._start_aggressive_reload()
            self.append_log('启动快速监控：1s × 8 次')
        except Exception:
            pass
        self.save_to_parent()

    def on_exit(self):
        try:
            if win32gui and self.target_hwnd:
                try:
                    self.restore_window_state(self.target_hwnd)
                except Exception:
                    pass
                self.target_hwnd = 0
        except Exception:
            pass
        self.save_to_parent()
        self.ensure_monitor_started()

    def on_close(self):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.remove_item(self)
        try:
            if win32gui and self.target_hwnd:
                self.restore_window_state(self.target_hwnd)
        except Exception:
            pass

    def capture_window_state(self, hwnd):
        try:
            st = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        except Exception:
            st = None
        try:
            est = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        except Exception:
            est = None
        try:
            pr = win32gui.GetParent(hwnd)
        except Exception:
            pr = None
        try:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            rect = (l, t, r, b)
        except Exception:
            rect = None
        try:
            placement = win32gui.GetWindowPlacement(hwnd)
        except Exception:
            placement = None
        self._orig = {'style': st, 'exstyle': est, 'parent': pr, 'rect': rect, 'placement': placement}

    def restore_window_state(self, hwnd):
        try:
            orig = getattr(self, '_orig', None)
            if not orig:
                # best-effort: reparent to desktop
                win32gui.SetParent(hwnd, win32gui.GetDesktopWindow())
                return
            try:
                if orig.get('parent'):
                    win32gui.SetParent(hwnd, orig['parent'])
                else:
                    win32gui.SetParent(hwnd, win32gui.GetDesktopWindow())
            except Exception:
                pass
            try:
                if orig.get('style') is not None:
                    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, orig['style'])
                if orig.get('exstyle') is not None:
                    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, orig['exstyle'])
            except Exception:
                pass
            try:
                if orig.get('rect'):
                    l, t, r, b = orig['rect']
                    win32gui.MoveWindow(hwnd, l, t, r - l, b - t, True)
            except Exception:
                pass
            try:
                # apply frame change and show normal
                win32gui.SetWindowPos(hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)
            except Exception:
                pass
            try:
                plc = orig.get('placement')
                if plc and isinstance(plc, tuple) and len(plc) >= 2:
                    win32gui.ShowWindow(hwnd, plc[1])
                else:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
            except Exception:
                pass
        except Exception:
            pass

    def hitHandle(self, pos):
        r = 8
        onRight = pos.x() >= self.width() - r
        onBottom = pos.y() >= self.height() - r
        if onRight and onBottom:
            return 'corner'
        if onRight:
            return 'right'
        if onBottom:
            return 'bottom'
        return None

    def mousePressEvent(self, e):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw and mw.locked:
            QFrame.mousePressEvent(self, e)
            return
        pos = e.position().toPoint()
        h = self.hitHandle(pos)
        if h:
            self.resizing = True
            self.resizeHandle = h
            self.resizeStart = pos
            self.startW = self.width()
            self.startH = self.height()
        else:
            self.dragging = True
            self.dragStart = pos
            self.raise_()
        QFrame.mousePressEvent(self, e)

    def mouseMoveEvent(self, e):
        if self.resizing:
            mw = self.parent()
            while mw and not isinstance(mw, MainWindow):
                mw = mw.parent()
            if mw:
                mw.compute_metrics()
                pos = e.position().toPoint()
                dx = pos.x() - self.resizeStart.x()
                dy = pos.y() - self.resizeStart.y()
                newW = self.startW
                newH = self.startH
                if self.resizeHandle in ('right','corner'):
                    newW = max(100, self.startW + dx)
                if self.resizeHandle in ('bottom','corner'):
                    newH = max(120, self.startH + dy)
                cellW = mw.cellW
                cellH = mw.cellH
                s = mw.gridSpacing
                gw = max(1, int(round((newW + s) / (cellW + s))))
                gh = max(1, int(round((newH + s) / (cellH + s))))
                while gw > 0 and (self.gridCol or 0) + gw > mw.gridCols:
                    gw -= 1
                if gw < 1:
                    gw = 1
                while mw.is_occupied_except(self, self.gridRow or 0, self.gridCol or 0, gw, gh):
                    if gw > 1:
                        gw -= 1
                    elif gh > 1:
                        gh -= 1
                    else:
                        break
                self.gridW = gw
                self.gridH = gh
                mw.place_card(self)
            QFrame.mouseMoveEvent(self, e)
            return
        if not self.dragging:
            pos = e.position().toPoint()
            h = self.hitHandle(pos)
            if h == 'right':
                self.setCursor(Qt.SizeHorCursor)
            elif h == 'bottom':
                self.setCursor(Qt.SizeVerCursor)
            elif h == 'corner':
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            QFrame.mouseMoveEvent(self, e)
            return
        pos = e.position().toPoint()
        dx = pos.x() - self.dragStart.x()
        dy = pos.y() - self.dragStart.y()
        self.move(self.x() + dx, self.y() + dy)
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.preview_snap(self)
        QFrame.mouseMoveEvent(self, e)

    def mouseReleaseEvent(self, e):
        if self.resizing:
            self.resizing = False
            mw = self.parent()
            while mw and not isinstance(mw, MainWindow):
                mw = mw.parent()
            if mw:
                mw.save_layout()
            QFrame.mouseReleaseEvent(self, e)
            return
        self.dragging = False
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.finish_snap(self)
        QFrame.mouseReleaseEvent(self, e)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('LZ-Panel')
        self.resize(1200, 800)
        try:
            self.setWindowFlag(Qt.FramelessWindowHint, True)
        except Exception:
            pass
        cw = QWidget()
        self.setCentralWidget(cw)
        outer = QVBoxLayout(cw)
        top = QHBoxLayout()
        self.urlInput = QLineEdit(self)
        self.addBtn = QPushButton('添加组件', self)
        self.addDesktopBtn = QPushButton('添加桌面组件', self)
        self.globalRefreshBtn = QPushButton('刷新检测', self)
        self.globalBindBtn = QPushButton('全局置入', self)
        self.saveBtn = QPushButton('保存', self)
        self.lockBtn = QPushButton('锁定布局', self)
        self.addCellBtn = QPushButton('添加格子', self)
        self.editToggleBtn = QPushButton('修改模式', self)
        self.fullToggleBtn = QPushButton('最大化', self)
        self.resizeToggleBtn = QPushButton('允许拖动大小', self)
        self.colSpin = QSpinBox(self)
        self.colSpin.setRange(1, 24)
        self.colSpin.setValue(6)
        self.rowSpin = QSpinBox(self)
        self.rowSpin.setRange(1, 999)
        self.rowSpin.setValue(4)
        
        top.addWidget(self.urlInput, 4)
        top.addWidget(QLabel('列数', self))
        top.addWidget(self.colSpin)
        top.addWidget(QLabel('行数', self))
        top.addWidget(self.rowSpin)
        
        top.addWidget(self.addBtn)
        top.addWidget(self.addDesktopBtn)
        top.addWidget(self.globalRefreshBtn)
        top.addWidget(self.globalBindBtn)
        top.addWidget(self.saveBtn)
        top.addWidget(self.addCellBtn)
        top.addWidget(self.editToggleBtn)
        top.addWidget(self.lockBtn)
        top.addWidget(self.fullToggleBtn)
        top.addWidget(self.resizeToggleBtn)
        self.tabs = QTabWidget(self)
        try:
            self.tabs.setTabsClosable(True)
            self.tabs.tabCloseRequested.connect(self.on_tab_close)
        except Exception:
            pass
        outer.addLayout(top)
        self.webProfile = QWebEngineProfile('CardGrid', self)
        try:
            prof_dir = os.path.join(DATA_DIR, 'web_profile')
            cache_dir = os.path.join(DATA_DIR, 'web_cache')
            os.makedirs(prof_dir, exist_ok=True)
            os.makedirs(cache_dir, exist_ok=True)
            self.webProfile.setPersistentStoragePath(prof_dir)
            self.webProfile.setCachePath(cache_dir)
            try:
                self.webProfile.setHttpUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36')
            except Exception:
                pass
            try:
                self.webProfile.setHttpAcceptLanguage('zh-CN,zh;q=0.9,en;q=0.8')
            except Exception:
                pass
            try:
                self.webProfile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            except Exception:
                pass
            try:
                self.webProfile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
            except Exception:
                pass
        except Exception:
            pass
        outer.addWidget(self.tabs)
        try:
            self.tray = QSystemTrayIcon(self)
            self.tray.setIcon(self.style().standardIcon(QStyle.SP_DesktopIcon))
            m = QMenu(self)
            a_show = QAction('显示/弹出', self)
            a_min = QAction('最小化', self)
            a_quit = QAction('退出', self)
            m.addAction(a_show)
            m.addAction(a_min)
            m.addAction(a_quit)
            self.tray.setContextMenu(m)
            a_show.triggered.connect(self.on_popup_shortcut)
            a_min.triggered.connect(self.on_min_shortcut)
            a_quit.triggered.connect(self.on_quit)
            self.tray.activated.connect(lambda r: self.on_popup_shortcut() if r == QSystemTrayIcon.Trigger else None)
            self.tray.show()
        except Exception:
            pass
        self.items = []
        self.pageItems = []
        self.pageScrolls = []
        self.pageContainers = []
        self.pageStates = []
        self.locked = False
        self.gridCols = 6
        self.gridSpacing = 12
        self.cellH = 240
        self.cellW = 300
        self.activeWeb = None
        self.gridRows = int(self.rowSpin.value())
        self.wasMinimized = False
        self.isFullscreen = False
        self.windowResizable = True
        self._wmResizing = False
        self._wmEdge = None
        self._wmStartGeom = None
        self._wmStartPos = None
        self.addPageBtn = QPushButton('新增页面', self)
        try:
            top.insertWidget(5, self.addPageBtn)
        except Exception:
            top.addWidget(self.addPageBtn)
        self.renamePageBtn = QPushButton('重命名页面', self)
        try:
            top.insertWidget(6, self.renamePageBtn)
        except Exception:
            top.addWidget(self.renamePageBtn)
        self.addBtn.clicked.connect(self.on_add)
        self.addDesktopBtn.clicked.connect(self.on_add_desktop)
        self.globalRefreshBtn.clicked.connect(self.on_global_refresh)
        self.globalBindBtn.clicked.connect(self.on_global_bind)
        self.saveBtn.clicked.connect(self.on_save)
        self.addPageBtn.clicked.connect(self.on_add_page)
        self.renamePageBtn.clicked.connect(self.on_rename_page)
        self.lockBtn.clicked.connect(self.on_lock)
        self.addCellBtn.clicked.connect(self.on_add_cell)
        self.editToggleBtn.clicked.connect(self.on_edit_toggle)
        self.fullToggleBtn.clicked.connect(self.on_toggle_fullscreen)
        self.resizeToggleBtn.clicked.connect(self.on_toggle_resizable)
        self.colSpin.valueChanged.connect(self.on_change_cols)
        self.rowSpin.valueChanged.connect(self.on_change_rows)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        try:
            cw.setMouseTracking(True)
            cw.installEventFilter(self)
        except Exception:
            pass
        self.load_layout()
        self.autoSave = False
        try:
            QTimer.singleShot(500, self._global_bind_on_start)
        except Exception:
            pass
        

    def on_add(self):
        if self.locked:
            return
        u = self.urlInput.text().strip()
        if not u:
            u = 'about:blank'
        w = 1
        h = 1
        self.add_card({'url': u, 'home': u, 'mode': 'in', 'collapsed': False, 'zoom': 1.0, 'scroll': 'hide', 'titleColor': '#1677ff', 'w': w, 'h': h})
        self.urlInput.setText('')
        self.save_layout()
    def on_add_cell(self):
        if self.locked:
            return
        w = 1
        h = 1
        self.add_spacer({'w': w, 'h': h})
        self.save_layout()
    def on_add_desktop(self):
        if self.locked:
            return
        w = 1
        h = 1
        self.add_desktop({'collapsed': False, 'titleColor': '#1677ff', 'w': w, 'h': h})
        self.save_layout()
    def on_save(self):
        try:
            self.save_layout(force=True)
        except Exception:
            pass
    def on_global_refresh(self):
        try:
            for it in list(self.items):
                try:
                    if isValid(it) and hasattr(it, 'refresh_windows') and hasattr(it, 'ensure_monitor_started'):
                        try:
                            it.refresh_windows()
                        except Exception:
                            pass
                        try:
                            it.try_auto_bind()
                        except Exception:
                            pass
                        it.ensure_monitor_started()
                        try:
                            it._monitor_tick()
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
    def on_global_bind(self):
        try:
            win_items = []
            if win32gui:
                def _cb(h, extra):
                    t = win32gui.GetWindowText(h)
                    try:
                        cls = win32gui.GetClassName(h)
                    except Exception:
                        cls = ''
                    if t:
                        win_items.append((h, t, cls))
                    return True
                try:
                    win32gui.EnumWindows(_cb, None)
                except Exception:
                    win_items = []
            def _norm(s: str) -> str:
                try:
                    import re
                    t = (s or '').strip()
                    t = re.sub(r"\s*[（(].*?[）)]\s*$", "", t)
                    return t.strip()
                except Exception:
                    return (s or '').strip()
            for it in list(self.items):
                try:
                    if not isValid(it):
                        continue
                    if isinstance(it, DesktopAppWidget):
                        want_label = (getattr(it, 'selLabel', '') or '').strip().lower()
                        LTL = _norm(getattr(it, 'lastTitle', '') or getattr(it, 'match', '')).lower()
                        LCL = (getattr(it, 'lastClass', '') or getattr(it, 'classMatch', '')).lower()
                        best = None
                        score = 0.0
                        for h, tt, cls in win_items:
                            lbl = (f"{(tt or '').strip()} ({(cls or '').strip()})" if cls else (tt or '').strip()).lower()
                            tl = _norm(tt or '').lower()
                            cl = (cls or '').lower()
                            s = 0.0
                            if want_label and lbl and lbl == want_label:
                                s = max(s, 2.0)
                            if LTL and LTL in tl:
                                s = max(s, 1.0)
                            if LCL and LCL in cl:
                                s = max(s, 1.0)
                            if LTL and tl:
                                try:
                                    s = max(s, difflib.SequenceMatcher(a=LTL, b=tl).ratio())
                                except Exception:
                                    pass
                            if LCL and cl:
                                try:
                                    s = max(s, difflib.SequenceMatcher(a=LCL, b=cl).ratio())
                                except Exception:
                                    pass
                            if s > score:
                                score = s
                                best = (h, tt, cls)
                        if best and score >= 0.6:
                            try:
                                it.selLabel = f"{best[1]} ({best[2]})" if best[2] else (best[1] or '')
                            except Exception:
                                pass
                            it.embed_window(int(best[0]))
                            try:
                                it.on_fit()
                            except Exception:
                                pass
                        continue
                    if isinstance(it, CardWidget):
                        try:
                            title = (getattr(it, 'titleLabel').text() if hasattr(it, 'titleLabel') else (getattr(it, 'title', '') or '')).strip()
                        except Exception:
                            title = (getattr(it, 'title', '') or '').strip()
                        want = _norm(title).lower()
                        best = None
                        score = 0.0
                        for h, tt, cls in win_items:
                            tl = _norm(tt or '').lower()
                            s = 0.0
                            if want and want in tl:
                                s = max(s, 1.0)
                            if want and tl:
                                try:
                                    s = max(s, difflib.SequenceMatcher(a=want, b=tl).ratio())
                                except Exception:
                                    pass
                            if s > score:
                                score = s
                                best = (h, tt, cls)
                        if best and score >= 0.6:
                            cfg = {
                                'collapsed': bool(getattr(it, 'collapsed', False)),
                                'title': title or '桌面',
                                'titleColor': getattr(it, 'titleColor', '#1677ff') or '#1677ff',
                                'match': '',
                                'regex': False,
                                'classMatch': '',
                                'classRegex': False,
                                'lastTitle': _norm(best[1]),
                                'lastClass': best[2],
                                'lastBounds': getattr(it, 'lastBounds', {}) if isinstance(getattr(it, 'lastBounds', {}), dict) else {},
                                'selLabel': f"{best[1]} ({best[2]})" if best[2] else (best[1] or ''),
                                'hwnd': int(best[0]),
                                'r': getattr(it, 'gridRow', -1),
                                'c': getattr(it, 'gridCol', -1),
                                'w': getattr(it, 'gridW', 1) or 1,
                                'h': getattr(it, 'gridH', 1) or 1
                            }
                            try:
                                self.remove_item(it)
                            except Exception:
                                pass
                            try:
                                self.add_desktop(cfg)
                                nd = self.items[-1] if self.items and isinstance(self.items[-1], DesktopAppWidget) else None
                                if nd and getattr(nd, 'target_hwnd', 0):
                                    try:
                                        nd.on_fit()
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass
    def _global_bind_on_start(self):
        try:
            n = self.tabs.count() if hasattr(self, 'tabs') else 1
            for i in range(max(1, n)):
                try:
                    if hasattr(self, 'tabs') and n > 0:
                        self.tabs.setCurrentIndex(i)
                    self.on_global_bind()
                except Exception:
                    pass
        except Exception:
            pass
    def on_quit(self):
        try:
            for it in list(self.items):
                try:
                    if isValid(it) and hasattr(it, 'target_hwnd') and getattr(it, 'target_hwnd', 0):
                        try:
                            it.restore_window_state(it.target_hwnd)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        try:
            os._exit(0)
        except Exception:
            try:
                QApplication.instance().quit()
            except Exception:
                pass
    def on_change_cols(self, val):
        self.gridCols = int(val)
        try:
            idx = self.tabs.currentIndex()
            if idx >= 0 and idx < len(self.pageStates):
                self.pageStates[idx]['gridCols'] = self.gridCols
        except Exception:
            pass
        self.compute_metrics()
        for it in self.items:
            if (getattr(it, 'gridCol', 0) or 0) + (getattr(it, 'gridW', 1) or 1) > self.gridCols:
                it.gridCol = max(0, self.gridCols - (getattr(it, 'gridW', 1) or 1))
        for it in self.items:
            self.place_card(it)
        self.save_layout()
    def on_change_rows(self, val):
        try:
            self.gridRows = int(val)
        except Exception:
            return
        try:
            idx = self.tabs.currentIndex()
            if idx >= 0 and idx < len(self.pageStates):
                self.pageStates[idx]['gridRows'] = self.gridRows
        except Exception:
            pass
        self.compute_metrics()
        for it in self.items:
            self.place_card(it)
        self.save_layout()
    def on_add_row(self):
        try:
            self.rowSpin.setValue(self.rowSpin.value() + 1)
        except Exception:
            pass
    def on_remove_row(self):
        try:
            if self.rowSpin.value() > 1:
                self.rowSpin.setValue(self.rowSpin.value() - 1)
        except Exception:
            pass

    def on_lock(self):
        self.locked = not self.locked
        self.lockBtn.setText('解锁布局' if self.locked else '锁定布局')
        self.addBtn.setEnabled(not self.locked)
        for c in self.items:
            c.editBtn.setEnabled(not self.locked)
        try:
            idx = self.tabs.currentIndex()
            if idx >= 0 and idx < len(self.pageStates):
                self.pageStates[idx]['locked'] = self.locked
        except Exception:
            pass

    def on_edit_toggle(self):
        if self.locked:
            return
        self.clean_items()
        any_editing = any(isValid(it) and getattr(it, 'editing', False) for it in self.items if isinstance(it, CardWidget) or isinstance(it, DesktopAppWidget))
        target = not any_editing
        for it in list(self.items):
            if not isValid(it):
                continue
            if isinstance(it, CardWidget) or isinstance(it, DesktopAppWidget):
                it.set_editing(target)
        self.editToggleBtn.setText('完成修改' if target else '修改模式')

    

    

    def on_popup_shortcut(self):
        try:
            if self.isMinimized() or not self.isVisible() or getattr(self, 'wasMinimized', False):
                self.showMaximized()
                self.wasMinimized = False
                self.raise_()
                self.activateWindow()
            else:
                self.raise_()
                self.activateWindow()
        except Exception:
            pass

    def on_min_shortcut(self):
        try:
            self.wasMinimized = True
            self.showMinimized()
        except Exception:
            pass

    def on_toggle_fullscreen(self):
        try:
            if not self.isFullscreen:
                self.showMaximized()
                self.isFullscreen = True
                self.fullToggleBtn.setText('窗口')
            else:
                self.showNormal()
                self.isFullscreen = False
                self.fullToggleBtn.setText('最大化')
        except Exception:
            pass

    def on_toggle_resizable(self):
        try:
            self.windowResizable = not self.windowResizable
            self.resizeToggleBtn.setText('允许拖动大小' if self.windowResizable else '禁止拖动大小')
            try:
                self.centralWidget().setCursor(Qt.ArrowCursor)
            except Exception:
                pass
        except Exception:
            pass

    

    

    

    

    

    

    def add_card(self, cfg):
        c = CardWidget(self.container, cfg)
        self.items.append(c)
        self.compute_metrics()
        if isinstance(cfg.get('r'), int) and cfg.get('r') >= 0 and isinstance(cfg.get('c'), int) and cfg.get('c') >= 0:
            c.gridRow = int(cfg.get('r'))
            c.gridCol = int(cfg.get('c'))
        else:
            gw = c.gridW if hasattr(c, 'gridW') and c.gridW else 1
            gh = c.gridH if hasattr(c, 'gridH') and c.gridH else 1
            r, col = self.find_free_slot(gw, gh)
            c.gridRow = r
            c.gridCol = col
        self.place_card(c)
        c.show()
    def add_spacer(self, cfg):
        s = SpacerWidget(self.container, cfg)
        self.items.append(s)
        self.compute_metrics()
        if isinstance(cfg.get('r'), int) and cfg.get('r') >= 0 and isinstance(cfg.get('c'), int) and cfg.get('c') >= 0:
            s.gridRow = int(cfg.get('r'))
            s.gridCol = int(cfg.get('c'))
        else:
            gw = s.gridW if hasattr(s, 'gridW') and s.gridW else 1
            gh = s.gridH if hasattr(s, 'gridH') and s.gridH else 1
            r, col = self.find_free_slot(gw, gh)
            s.gridRow = r
            s.gridCol = col
        self.place_card(s)
        s.show()
    def add_desktop(self, cfg):
        d = DesktopAppWidget(self.container, cfg)
        self.items.append(d)
        self.compute_metrics()
        if isinstance(cfg.get('r'), int) and cfg.get('r') >= 0 and isinstance(cfg.get('c'), int) and cfg.get('c') >= 0:
            d.gridRow = int(cfg.get('r'))
            d.gridCol = int(cfg.get('c'))
        else:
            gw = d.gridW if hasattr(d, 'gridW') and d.gridW else 1
            gh = d.gridH if hasattr(d, 'gridH') and d.gridH else 1
            r, col = self.find_free_slot(gw, gh)
            d.gridRow = r
            d.gridCol = col
        self.place_card(d)
        d.show()
    def on_tab_changed(self, idx):
        try:
            self.set_current_page(idx)
        except Exception:
            pass
    def on_add_page(self):
        try:
            name = f"页面 {self.tabs.count()+1}"
            st = {'gridCols': int(self.colSpin.value()), 'gridRows': int(self.rowSpin.value()), 'locked': False}
            self._create_page(name, st)
            self.tabs.setCurrentIndex(self.tabs.count()-1)
        except Exception:
            pass
    def on_rename_page(self):
        try:
            idx = self.tabs.currentIndex()
            if idx < 0:
                return
            old = self.tabs.tabText(idx)
            text, ok = QInputDialog.getText(self, '重命名页面', '页面名称：', text=old)
            if ok:
                t = (text or '').strip()
                if t:
                    self.tabs.setTabText(idx, t)
                    self.save_layout()
        except Exception:
            pass
    def on_tab_close(self, idx):
        try:
            if self.tabs.count() <= 1:
                return
            try:
                lst = self.pageItems[idx] if idx < len(self.pageItems) else []
                for it in list(lst):
                    try:
                        if isValid(it):
                            it.deleteLater()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                sa = self.pageScrolls.pop(idx)
                cont = self.pageContainers.pop(idx)
                self.pageItems.pop(idx)
                self.pageStates.pop(idx)
                try:
                    if isValid(sa):
                        sa.deleteLater()
                except Exception:
                    pass
                try:
                    if isValid(cont):
                        cont.deleteLater()
                except Exception:
                    pass
            except Exception:
                pass
            try:
                self.tabs.removeTab(idx)
            except Exception:
                pass
            try:
                ni = max(0, min(idx, self.tabs.count()-1))
                self.set_current_page(ni)
            except Exception:
                pass
            self.save_layout()
        except Exception:
            pass
    def _create_page(self, name: str, state: dict | None = None):
        sa = QScrollArea(self)
        try:
            sa.setWidgetResizable(True)
            sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sa.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except Exception:
            pass
        cont = GridContainer(self)
        try:
            cont.setMouseTracking(True)
        except Exception:
            pass
        try:
            sa.setWidget(cont)
        except Exception:
            pass
        try:
            self.tabs.addTab(sa, name or f"页面 {self.tabs.count()+1}")
        except Exception:
            pass
        self.pageScrolls.append(sa)
        self.pageContainers.append(cont)
        self.pageItems.append([])
        st = state or {'gridCols': 6, 'gridRows': 4, 'locked': False}
        self.pageStates.append({'gridCols': int(st.get('gridCols', 6)), 'gridRows': int(st.get('gridRows', 4)), 'locked': bool(st.get('locked', False))})
        if self.tabs.count() == 1:
            try:
                self.set_current_page(0)
            except Exception:
                pass
    def set_current_page(self, idx: int):
        if idx < 0 or idx >= len(self.pageScrolls):
            return
        self.scrollArea = self.pageScrolls[idx]
        self.container = self.pageContainers[idx]
        self.items = self.pageItems[idx]
        st = self.pageStates[idx]
        self.gridCols = int(st.get('gridCols', 6))
        self.gridRows = int(st.get('gridRows', 4))
        self.locked = bool(st.get('locked', False))
        try:
            self.colSpin.setValue(self.gridCols)
        except Exception:
            pass
        try:
            self.rowSpin.setValue(self.gridRows)
        except Exception:
            pass
        try:
            self.lockBtn.setText('解锁布局' if self.locked else '锁定布局')
            self.addBtn.setEnabled(not self.locked)
            for c in list(self.items):
                if isValid(c):
                    try:
                        c.editBtn.setEnabled(not self.locked)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            self.compute_metrics()
            self.clean_items()
            for it in list(self.items):
                if isValid(it):
                    self.place_card(it)
        except Exception:
            pass

    def load_layout(self):
        data = load_layout()
        pages = data.get('pages') if isinstance(data.get('pages'), list) else None
        if pages:
            for pg in pages:
                name = pg.get('name') or f"页面 {self.tabs.count()+1}"
                st = {'gridCols': pg.get('gridCols', 6), 'gridRows': pg.get('gridRows', 4), 'locked': pg.get('locked', False)}
                self._create_page(name, st)
                try:
                    idx = self.tabs.count()-1
                    self.set_current_page(idx)
                except Exception:
                    pass
                for it in pg.get('items', []):
                    try:
                        t = it.get('type')
                        if t == 'spacer':
                            self.add_spacer(it)
                        elif t == 'desktop':
                            self.add_desktop(it)
                        else:
                            self.add_card(it)
                    except Exception:
                        pass
            try:
                self.set_current_page(0)
            except Exception:
                pass
        else:
            st = {'gridCols': data.get('gridCols', 6), 'gridRows': data.get('gridRows', 4), 'locked': data.get('locked', False)}
            self._create_page('页面 1', st)
            try:
                self.set_current_page(0)
            except Exception:
                pass
            for it in data.get('items', []):
                t = it.get('type')
                if t == 'spacer':
                    self.add_spacer(it)
                elif t == 'desktop':
                    self.add_desktop(it)
                else:
                    self.add_card(it)

    def save_layout(self, force: bool = False):
        if not force and not getattr(self, 'autoSave', False):
            return
        pages = []
        try:
            for i in range(len(self.pageItems)):
                items = []
                for c in list(self.pageItems[i]):
                    if not isValid(c):
                        continue
                    items.append(c.to_dict())
                st = self.pageStates[i] if i < len(self.pageStates) else {'gridCols': 6, 'gridRows': 4, 'locked': False}
                name = self.tabs.tabText(i) if i < self.tabs.count() else f"页面 {i+1}"
                pages.append({'name': name, 'locked': bool(st.get('locked', False)), 'gridCols': int(st.get('gridCols', 6)), 'gridRows': int(st.get('gridRows', 4)), 'items': items})
        except Exception:
            pass
        data = {'pages': pages}
        save_layout(data)
    def compute_metrics(self):
        w = self.scrollArea.viewport().width()
        self.viewportW = w
        available = max(0, w - (self.gridCols - 1) * self.gridSpacing)
        self.cellW = max(1, int(available / self.gridCols))
    def place_card(self, c):
        self.compute_metrics()
        c.setParent(self.container)
        gw = c.gridW if hasattr(c, 'gridW') and c.gridW else 1
        gh = c.gridH if hasattr(c, 'gridH') and c.gridH else 1
        w = gw * self.cellW + (gw - 1) * self.gridSpacing
        h = gh * self.cellH + (gh - 1) * self.gridSpacing
        c.setFixedSize(w, h)
        x = (c.gridCol or 0) * (self.cellW + self.gridSpacing)
        y = (c.gridRow or 0) * (self.cellH + self.gridSpacing)
        c.move(x, y)
        self.clean_items()
        rows_needed = 1 + max([(it.gridRow or 0) + (getattr(it, 'gridH', 1) or 1) - 1 for it in self.items if isValid(it)] or [0])
        rows_target = max(rows_needed, self.gridRows)
        cont_w = self.viewportW
        cont_h = rows_target * self.cellH + (rows_target - 1) * self.gridSpacing
        self.container.setMinimumSize(cont_w, cont_h)
        self.container.resize(cont_w, cont_h)
        self.container.update()
        if self.scrollArea and self.scrollArea.viewport():
            self.scrollArea.viewport().update()
    def find_free_slot(self, w, h):
        w = min(w, self.gridCols)
        self.compute_metrics()
        max_rows = 1 + max([(it.gridRow or 0) + (getattr(it, 'gridH', 1) or 1) - 1 for it in self.items] or [0])
        row = 0
        while True:
            for col in range(0, max(1, self.gridCols - w + 1)):
                if not self.is_occupied_except(None, row, col, w, h):
                    return row, col
            row += 1
            if row > max_rows + 100:
                return max_rows + 1, 0
    def preview_snap(self, c):
        pass
    def finish_snap(self, c):
        if self.locked:
            return
        self.compute_metrics()
        self.clean_items()
        cx = c.x() + c.width() // 2
        cy = c.y() + c.height() // 2
        stepX = self.cellW + self.gridSpacing
        stepY = self.cellH + self.gridSpacing
        col_center = int(round(cx / stepX))
        row_center = int(round(cy / stepY))
        gw = c.gridW or 1
        gh = c.gridH or 1
        col = max(0, min(self.gridCols - gw, col_center - (gw // 2)))
        row = max(0, row_center - (gh // 2))
        if self.is_occupied_except(c, row, col, c.gridW or 1, c.gridH or 1):
            row = c.gridRow or 0
            col = c.gridCol or 0
        old_r, old_c = c.gridRow, c.gridCol
        c.gridRow, c.gridCol = row, col
        self.items[:] = [it for it in self.items if isValid(it)]
        self.items.sort(key=lambda i: (i.gridRow, i.gridCol))
        for it in list(self.items):
            if not isValid(it):
                continue
            self.place_card(it)
        self.save_layout()
    def is_occupied_except(self, ignore, row, col, w, h):
        for it in list(self.items):
            if not isValid(it):
                continue
            if it is ignore:
                continue
            r2 = it.gridRow or 0
            c2 = it.gridCol or 0
            w2 = getattr(it, 'gridW', 1) or 1
            h2 = getattr(it, 'gridH', 1) or 1
            if (row < r2 + h2 and row + h > r2) and (col < c2 + w2 and col + w > c2):
                return True
        return False
    def resizeEvent(self, e):
        QMainWindow.resizeEvent(self, e)
        self.compute_metrics()
        self.clean_items()
        for it in list(self.items):
            if not isValid(it):
                continue
            self.place_card(it)

    def showEvent(self, e):
        try:
            QMainWindow.showEvent(self, e)
        except Exception:
            pass
        try:
            if getattr(self, 'wasMinimized', False):
                self.showMaximized()
                self.wasMinimized = False
        except Exception:
            pass

    def eventFilter(self, obj, ev):
        try:
            if obj is self.centralWidget():
                if ev.type() == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
                    if self.windowResizable and not self.isFullscreen:
                        gp = obj.mapToGlobal(ev.position().toPoint())
                        edge = self._hit_window_edge(gp)
                        if edge:
                            self._wmResizing = True
                            self._wmEdge = edge
                            self._wmStartGeom = self.frameGeometry()
                            self._wmStartPos = gp
                            return True
                elif ev.type() == QEvent.MouseMove:
                    if self._wmResizing and self.windowResizable and not self.isFullscreen:
                        gp = obj.mapToGlobal(ev.position().toPoint())
                        dx = gp.x() - self._wmStartPos.x()
                        dy = gp.y() - self._wmStartPos.y()
                        g = self._wmStartGeom
                        r = g
                        if self._wmEdge in ('left','lt','lb'):
                            nl = r.left() + dx
                            if r.right() - nl < self.minimumWidth():
                                nl = r.right() - self.minimumWidth()
                            r.setLeft(nl)
                        if self._wmEdge in ('right','rt','rb'):
                            nr = r.right() + dx
                            if nr - r.left() < self.minimumWidth():
                                nr = r.left() + self.minimumWidth()
                            r.setRight(nr)
                        if self._wmEdge in ('top','lt','rt'):
                            nt = r.top() + dy
                            if r.bottom() - nt < self.minimumHeight():
                                nt = r.bottom() - self.minimumHeight()
                            r.setTop(nt)
                        if self._wmEdge in ('bottom','lb','rb'):
                            nb = r.bottom() + dy
                            if nb - r.top() < self.minimumHeight():
                                nb = r.top() + self.minimumHeight()
                            r.setBottom(nb)
                        self.setGeometry(r)
                        return True
                    else:
                        if self.windowResizable and not self.isFullscreen:
                            gp = obj.mapToGlobal(ev.position().toPoint())
                            edge = self._hit_window_edge(gp)
                            if edge in ('left','right'):
                                obj.setCursor(Qt.SizeHorCursor)
                            elif edge in ('top','bottom'):
                                obj.setCursor(Qt.SizeVerCursor)
                            elif edge in ('lt','rb'):
                                obj.setCursor(Qt.SizeFDiagCursor)
                            elif edge in ('rt','lb'):
                                obj.setCursor(Qt.SizeBDiagCursor)
                            else:
                                obj.setCursor(Qt.ArrowCursor)
                elif ev.type() == QEvent.MouseButtonRelease and ev.button() == Qt.LeftButton:
                    if self._wmResizing:
                        self._wmResizing = False
                        self._wmEdge = None
                        try:
                            obj.setCursor(Qt.ArrowCursor)
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            return QMainWindow.eventFilter(self, obj, ev)
        except Exception:
            return False

    def _hit_window_edge(self, global_pos):
        try:
            g = self.frameGeometry()
            th = 8
            x = global_pos.x()
            y = global_pos.y()
            l = abs(x - g.left()) <= th
            r = abs(x - g.right()) <= th
            t = abs(y - g.top()) <= th
            b = abs(y - g.bottom()) <= th
            if l and t:
                return 'lt'
            if r and t:
                return 'rt'
            if l and b:
                return 'lb'
            if r and b:
                return 'rb'
            if l:
                return 'left'
            if r:
                return 'right'
            if t:
                return 'top'
            if b:
                return 'bottom'
            return None
        except Exception:
            return None

    

    def closeEvent(self, e):
        try:
            self.on_quit()
        except Exception:
            pass
        try:
            e.accept()
        except Exception:
            pass

    def clean_items(self):
        self.items[:] = [it for it in self.items if isValid(it)]

    def remove_item(self, widget):
        try:
            self.items[:] = [it for it in self.items if it is not widget and isValid(it)]
            widget.deleteLater()
            self.save_layout()
            self.compute_metrics()
            self.clean_items()
            for it in list(self.items):
                if not isValid(it):
                    continue
                self.place_card(it)
        except Exception:
            pass

def main():
    ensure_data()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
    
    
