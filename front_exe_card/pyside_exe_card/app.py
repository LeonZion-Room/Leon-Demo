import os
import sys
import json
from PySide6.QtCore import Qt, QUrl, QEvent
from PySide6.QtGui import QColor, QPainter, QDesktopServices
from shiboken6 import isValid
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QSlider, QColorDialog, QScrollArea, QFrame, QSpinBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript, QWebEngineProfile

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
LAYOUT_PATH = os.path.join(DATA_DIR, 'layout.json')

def ensure_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LAYOUT_PATH):
        with open(LAYOUT_PATH, 'w', encoding='utf-8') as f:
            json.dump({"locked": False, "items": []}, f, ensure_ascii=False, indent=2)

def load_layout():
    ensure_data()
    with open(LAYOUT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_layout(data):
    os.makedirs(DATA_DIR, exist_ok=True)
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
        self.mode = self.config.get('mode') or 'in'
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
        self.modeSel.setCurrentIndex(0 if self.mode=='in' else 1)
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
        self.web.installEventFilter(self)
        bodyWrap.addWidget(self.web)
        v.addLayout(bodyWrap)
        self.apply_collapsed()
        self.apply_zoom(self.zoom)
        self.navigate(self.current, push=False)
        self.editing = False
        self.inputs.setEnabled(False)
        self.editBtn.clicked.connect(self.toggle_edit)
        self.toggleBtn.clicked.connect(self.toggle_collapse)
        self.backBtn.clicked.connect(self.web.back)
        self.fwdBtn.clicked.connect(self.web.forward)
        self.homeBtn.clicked.connect(lambda: self.navigate(self.home, push=True))
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

    def apply_zoom(self, z):
        self.web.setZoomFactor(z)

    def on_go(self):
        u = self.urlEdit.text().strip()
        if not u:
            return
        if self.mode == 'out':
            QDesktopServices.openUrl(QUrl(u))
        else:
            self.navigate(u, push=True)

    def navigate(self, url, push=True):
        self.current = url
        self.titleLabel.setText(self.default_title())
        self.web.load(QUrl(url))
        self.inject_scripts()
        if push:
            self.save_to_parent()

    def inject_scripts(self):
        hide_css = "html,body{overflow:hidden!important;} ::-webkit-scrollbar{width:0!important;height:0!important;display:none!important;}"
        js = """
        (function(){try{
          document.querySelectorAll('a[target="_blank"]').forEach(function(a){a.setAttribute('target','_self');});
          window.open = function(u){location.href=u;};
          document.addEventListener('click',function(e){var a=e.target.closest('a[href]'); if(a){a.setAttribute('target','_self');}});
        }catch(e){}})();
        """
        if self.scroll == 'hide':
            css_js = f"(function(){{try{{var s=document.getElementById('__hide_scroll__');if(!s){{s=document.createElement('style');s.id='__hide_scroll__';s.textContent='{hide_css}';document.head.appendChild(s);}}}}catch(e){{}}}})();"
            self.web.page().runJavaScript(css_js)
        self.web.page().runJavaScript(js)

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

    def on_close(self):
        mw = self.parent()
        while mw and not isinstance(mw, MainWindow):
            mw = mw.parent()
        if mw:
            mw.remove_item(self)

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
        self.closeBtn.clicked.connect(self.deleteLater)
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('LZ-Panel')
        self.resize(1200, 800)
        cw = QWidget()
        self.setCentralWidget(cw)
        outer = QVBoxLayout(cw)
        top = QHBoxLayout()
        self.urlInput = QLineEdit(self)
        self.addBtn = QPushButton('添加组件', self)
        self.lockBtn = QPushButton('锁定布局', self)
        self.addCellBtn = QPushButton('添加格子', self)
        self.editToggleBtn = QPushButton('修改模式', self)
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
        top.addWidget(self.addCellBtn)
        top.addWidget(self.editToggleBtn)
        top.addWidget(self.lockBtn)
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
                self.webProfile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            except Exception:
                pass
            try:
                self.webProfile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
            except Exception:
                pass
        except Exception:
            pass
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = GridContainer(self)
        self.container.setMouseTracking(True)
        self.scrollArea.setWidget(self.container)
        outer.addWidget(self.scrollArea)
        self.items = []
        self.locked = False
        self.gridCols = 6
        self.gridSpacing = 12
        self.cellH = 240
        self.cellW = 300
        self.activeWeb = None
        self.gridRows = int(self.rowSpin.value())
        self.addBtn.clicked.connect(self.on_add)
        self.lockBtn.clicked.connect(self.on_lock)
        self.addCellBtn.clicked.connect(self.on_add_cell)
        self.editToggleBtn.clicked.connect(self.on_edit_toggle)
        self.colSpin.valueChanged.connect(self.on_change_cols)
        self.rowSpin.valueChanged.connect(self.on_change_rows)
        self.load_layout()
        

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
    def on_change_cols(self, val):
        self.gridCols = int(val)
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

    def on_edit_toggle(self):
        if self.locked:
            return
        self.clean_items()
        any_editing = any(isValid(it) and getattr(it, 'editing', False) for it in self.items if isinstance(it, CardWidget))
        target = not any_editing
        for it in list(self.items):
            if not isValid(it):
                continue
            if isinstance(it, CardWidget):
                it.set_editing(target)
        self.editToggleBtn.setText('完成修改' if target else '修改模式')

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

    def load_layout(self):
        data = load_layout()
        if isinstance(data.get('gridCols'), int) and data.get('gridCols') > 0:
            self.gridCols = int(data.get('gridCols'))
            try:
                self.colSpin.setValue(self.gridCols)
            except Exception:
                pass
        if isinstance(data.get('gridRows'), int) and data.get('gridRows') > 0:
            self.gridRows = int(data.get('gridRows'))
            try:
                self.rowSpin.setValue(self.gridRows)
            except Exception:
                pass
        self.locked = bool(data.get('locked', False))
        self.lockBtn.setText('解锁布局' if self.locked else '锁定布局')
        self.addBtn.setEnabled(not self.locked)
        for it in data.get('items', []):
            if it.get('type') == 'spacer':
                self.add_spacer(it)
            else:
                self.add_card(it)

    def save_layout(self):
        self.clean_items()
        items = []
        for c in list(self.items):
            if not isValid(c):
                continue
            if c.isHidden():
                continue
            items.append(c.to_dict())
        data = {'locked': self.locked, 'gridCols': self.gridCols, 'gridRows': self.gridRows, 'items': items}
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
        self.items = [it for it in self.items if isValid(it)]
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

    def closeEvent(self, e):
        try:
            self.save_layout()
        except Exception:
            pass
        return QMainWindow.closeEvent(self, e)

    def clean_items(self):
        self.items = [it for it in self.items if isValid(it)]

    def remove_item(self, widget):
        try:
            self.items = [it for it in self.items if it is not widget and isValid(it)]
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
