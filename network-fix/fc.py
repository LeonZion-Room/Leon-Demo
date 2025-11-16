import sys
import os
import webbrowser
import urllib.request
import urllib.parse

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QProgressBar, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QFont


class ImageCoverWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        painter.end()


class FullScreenImageWindow(QMainWindow):
    def __init__(self, image_path_or_url: str, target_url: str):
        super().__init__()
        self.target_url = target_url
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # 中心容器与布局
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 图片区域（按比例覆盖窗口）
        self.image = ImageCoverWidget(container)
        layout.addWidget(self.image, stretch=1)

        # 底部倒计时进度条（更显著，左→右递增）
        self.progress = QProgressBar(container)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setAlignment(Qt.AlignCenter)
        self.progress.setFixedHeight(12)
        self.progress.setStyleSheet(
            "QProgressBar{border:0;background:rgba(0,0,0,130);color:white;}" 
            "QProgressBar::chunk{background:#00c853;}"
        )
        layout.addWidget(self.progress, stretch=0)

        self.setCentralWidget(container)
        self.setCursor(Qt.PointingHandCursor)

        pixmap = self.load_image(image_path_or_url)
        self.original_pixmap = pixmap
        self.adjust_initial_size_and_center(pixmap)
        self.image.setPixmap(self.original_pixmap)

        # 倒计时（3秒）在窗口显示时启动
        self._countdown_ms = 3000
        self._interval_ms = 50
        self._countdown_started = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def load_image(self, image_path_or_url: str) -> QPixmap:
        screen = QApplication.primaryScreen()
        size = screen.size() if screen else QSize(1920, 1080)


        def _clean_src(s: str) -> str:
            return (s or "").strip().strip("`")

        def _fetch_image_bytes(url: str) -> bytes | None:
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                })
                with urllib.request.urlopen(req, timeout=8) as resp:
                    ct = resp.headers.get("Content-Type", "").lower()
                    data = resp.read()
                    if "image" in ct:
                        return data
                    # 尝试从 HTML 中提取 og:image
                    try:
                        html = data.decode("utf-8", errors="ignore")
                        import re
                        m = re.search(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']", html, re.I)
                        if not m:
                            m = re.search(r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+property=[\"']og:image[\"']", html, re.I)
                        if m:
                            img_url = urllib.parse.urljoin(url, m.group(1))
                            return _fetch_image_bytes(img_url)
                    except Exception:
                        pass
                    return None
            except Exception:
                return None

        pixmap = None
        src = _clean_src(image_path_or_url or "")
        if src:
            if src.startswith("http://") or src.startswith("https://"):
                data = _fetch_image_bytes(src)
                if data:
                    p = QPixmap()
                    if p.loadFromData(data):
                        pixmap = p
            else:
                # 支持 file:// 协议与本地路径
                if src.startswith("file://"):
                    local_path = urllib.parse.urlparse(src).path
                    if os.path.exists(local_path):
                        pixmap = QPixmap(local_path)
                elif os.path.exists(src):
                    pixmap = QPixmap(src)

        if not pixmap or pixmap.isNull():
            pixmap = self._create_placeholder_pixmap(size)

        return pixmap

    def _create_placeholder_pixmap(self, size: QSize) -> QPixmap:
        pixmap = QPixmap(size)
        pixmap.fill(Qt.black)
        painter = QPainter(pixmap)
        grad = QLinearGradient(0, 0, size.width(), size.height())
        grad.setColorAt(0.0, QColor(40, 100, 180))
        grad.setColorAt(1.0, QColor(20, 40, 80))
        painter.fillRect(0, 0, size.width(), size.height(), grad)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 28)
        painter.setFont(font)
        text = "点击打开: " + self.target_url
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return pixmap

    def adjust_initial_size_and_center(self, pixmap: QPixmap):
        # 改为：非全屏，按图片比例计算目标尺寸并居中显示
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            max_size = QSize(int(avail.width() * 0.25), int(avail.height() * 0.25))
        else:
            max_size = QSize(960, 540)
        target_size = pixmap.size().scaled(max_size, Qt.KeepAspectRatio)
        self.resize(target_size)
        # 居中窗口
        if screen:
            fg = self.frameGeometry()
            fg.moveCenter(screen.availableGeometry().center())
            self.move(fg.topLeft())

    def resizeEvent(self, event):
        self._update_label_pixmap()
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._countdown_started:
            self._countdown_started = True
            self._remaining_ms = self._countdown_ms
            self._elapsed_ms = 0
            self.progress.setValue(0)
            self.progress.setFormat("加载中 %p%")
            self.progress.show()
            self._timer.start(self._interval_ms)

    def _on_tick(self):
        self._remaining_ms -= self._interval_ms
        self._elapsed_ms += self._interval_ms
        percent = max(0, min(100, int(self._elapsed_ms * 100 / self._countdown_ms)))
        self.progress.setValue(percent)
        if self._remaining_ms <= 0:
            self._timer.stop()
            self.progress.hide()
            self.close()

    def _update_label_pixmap(self):
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            self.image.setPixmap(self.original_pixmap)

    def mousePressEvent(self, event):
        webbrowser.open(self.target_url)
        self.close()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)


def show_fullscreen_image_and_open_url(image_path_or_url: str, target_url: str) -> None:
    # 改为：普通窗口居中显示，图片按比例覆盖窗口；延迟 3 秒显示
    app = QApplication.instance() or QApplication(sys.argv)
    win = FullScreenImageWindow(image_path_or_url, target_url)
    QTimer.singleShot(3000, win.show)
    app.exec_()



def _prepare_icon_path(icon_path_or_url: str | None, resize_to: int | None = None) -> str | None:
    if not icon_path_or_url:
        return None
    try:
        img: Image.Image | None = None
        if icon_path_or_url.startswith("http://") or icon_path_or_url.startswith("https://"):
            data = urllib.request.urlopen(icon_path_or_url, timeout=6).read()
            bio = io.BytesIO(data)
            img = Image.open(bio)
        else:
            if not os.path.exists(icon_path_or_url):
                return None
            img = Image.open(icon_path_or_url)

        if img is None:
            return None

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        if resize_to and resize_to > 0:
            img = img.resize((resize_to, resize_to), Image.LANCZOS)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img.save(tmp, format="PNG")
        tmp.flush()
        tmp.close()
        return tmp.name
    except Exception:
        return None


def show_windows_toast(title: str, message: str, duration: int = 5, icon: str | None = None, url: str | None = None, button_label: str | None = None, icon_size: int | None = None) -> None:
    icon_path = _prepare_icon_path(icon, resize_to=icon_size)
    try:
        from winotify import Notification, audio
        d = "short" if duration <= 5 else "long"
        toast = Notification(app_id="Leon-PyQt-Demo", title=title, msg=message, icon=icon_path, duration=d)
        toast.set_audio(audio.Default, loop=False)
        if url:
            toast.add_actions(label=button_label or "打开链接", launch=url)
        toast.show()
        return
    except Exception:
        pass

    # 回退：win10toast（不支持点击跳转；icon 需为本地路径）
    try:
        from win10toast import ToastNotifier
        notifier = ToastNotifier()
        notifier.show_toast(title, message, icon_path=icon_path, duration=duration, threaded=False)
    except Exception as e:
        print("Toast 发送失败:", e)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="无边框全屏图片，点击跳转网页；Windows Toast 通知")
    parser.add_argument("--image", dest="image", default="", help="本地图片路径或 http 链接")
    parser.add_argument("--url", dest="url", default="https://www.baidu.com", help="点击后打开的网页地址")
    parser.add_argument("--toast-title", dest="toast_title", default="", help="Toast 标题")
    parser.add_argument("--toast-message", dest="toast_message", default="", help="Toast 内容")
    args = parser.parse_args()

   ##  if args.toast_title or args.toast_message:
       #  show_windows_toast(args.toast_title or "提示", args.toast_message or "这是一条通知")

    # show_fullscreen_image_and_open_url(args.image, args.url)