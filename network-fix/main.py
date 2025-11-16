import os
import sys
import time
import ctypes
import threading
import queue
import subprocess
import locale
import re
import tkinter as tk
import webbrowser
import urllib.request
from fc import FullScreenImageWindow, show_windows_toast

def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate_if_needed():
    if is_admin():
        return
    params = "{} {}".format(os.path.abspath(__file__), " ".join(sys.argv[1:])).strip()
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    if rc <= 32:
        raise RuntimeError("无法获取管理员权限（UAC 提升失败）")
    # 重新启动为管理员后，当前非管理员进程退出，避免双实例
    sys.exit(0)


def _first(value):
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return value


def _venv_pip_path() -> str | None:
    base = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(base, ".venv", "Scripts", "pip.exe")
    if os.path.exists(cand):
        return cand
    cand2 = os.path.join(base, ".venv", "Scripts", "pip")
    if os.path.exists(cand2):
        return cand2
    return None


def _install_package(pkg_name: str) -> bool:
    mirror = "https://mirrors.aliyun.com/pypi/simple/"
    pip_path = _venv_pip_path()
    if pip_path:
        args = [pip_path, "install", "-i", mirror, pkg_name]
    else:
        args = [sys.executable, "-m", "pip", "install", "-i", mirror, pkg_name]
    proc = subprocess.run(args, capture_output=True)
    return proc.returncode == 0


def ensure_module(mod_name: str, pkg_name: str | None = None) -> bool:
    import importlib
    try:
        importlib.import_module(mod_name)
        return True
    except ImportError:
        ok = _install_package(pkg_name or mod_name)
        if not ok:
            return False
        try:
            importlib.import_module(mod_name)
            return True
        except ImportError:
            return False


class WmiNetworkFixerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("网络修复工具")
        self.root.geometry("720x480")

        self.log_queue = queue.Queue()
        self.total_steps = 0
        self.current_step = 0
        self.worker = None

        # UI 组件
        top = tb.Frame(root, padding=10)
        top.pack(fill=tk.X)

        self.btn_start = tb.Button(top, text="开始修复", command=self.start_fix, bootstyle="primary")
        self.btn_start.pack(side=tk.LEFT)

        self.auto_connect_var = tk.BooleanVar(value=True)
        self.chk_auto = tb.Checkbutton(top, text="自动连接最强已保存 Wi-Fi", variable=self.auto_connect_var, bootstyle="info")
        self.chk_auto.pack(side=tk.LEFT, padx=8)

        self.auto_connect_lan_var = tk.BooleanVar(value=True)
        self.chk_auto_lan = tb.Checkbutton(top, text="自动连接最强有线", variable=self.auto_connect_lan_var, bootstyle="info")
        self.chk_auto_lan.pack(side=tk.LEFT)

        self.btn_exit = tb.Button(top, text="退出", command=root.destroy, bootstyle="danger")
        self.btn_exit.pack(side=tk.LEFT, padx=8)

        self.status_var = tk.StringVar(value="就绪：点击“开始修复”执行")
        self.lbl_status = tb.Label(top, textvariable=self.status_var)
        self.lbl_status.pack(side=tk.RIGHT)

        mid = tb.Frame(root, padding=10)
        mid.pack(fill=tk.X)

        self.progress = tb.Progressbar(mid, mode="determinate", bootstyle="info-striped")
        self.progress.pack(fill=tk.X)

        bottom = tb.Frame(root, padding=10)
        bottom.pack(fill=tk.BOTH, expand=True)

        self.log_text = ScrolledText(bottom, wrap=tk.WORD, height=18)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 定时从队列刷新日志/状态/进度
        self.root.after(100, self._drain_queue)

    def start_fix(self):
        if self.worker and self.worker.is_alive():
            return
        self.status_var.set("执行中…")
        self.progress.configure(value=0, maximum=100)
        self.current_step = 0
        self.total_steps = 0
        self.btn_start.configure(state=tk.DISABLED)
        self._log("开始执行网络修复…")
        self.worker = threading.Thread(target=self._run_fix, daemon=True)
        self.worker.start()

    def _run_fix(self):
        # 先确保依赖可用
        try:
            import wmi  # type: ignore
        except ImportError:
            self._log("缺少 wmi 依赖。请先在虚拟环境中安装：")
            self._log(".venv\\Scripts\\pip install -i https://mirrors.aliyun.com/pypi/simple/ wmi")
            self._done(status="依赖缺失")
            return

        # 主执行逻辑包裹在 try/except，统一错误展示
        try:
            c = wmi.WMI()
            cfg_by_index = {cfg.Index: cfg for cfg in c.Win32_NetworkAdapterConfiguration()}

            targets = []
            for nic in c.Win32_NetworkAdapter(PhysicalAdapter=True):
                # 仅处理以太网(0)和无线(9)
                if nic.AdapterTypeID not in (0, 9):
                    continue
                alias = nic.NetConnectionID or nic.Name or f"Index {nic.Index}"
                if alias and alias.lower() and ("bluetooth" in alias.lower() or "蓝牙" in alias.lower()):
                    # 排除蓝牙 PAN 等伪以太网
                    continue
                cfg = cfg_by_index.get(nic.Index)
                if not cfg:
                    continue
                targets.append((alias, nic, cfg))

            if not targets:
                self._log("未发现物理有线/无线网卡")
                self._done(status="无网卡")
                return

            self._log("发现网卡: " + ", ".join([alias for alias, _, _ in targets]))
            self.total_steps = (
                len(targets) * 2
                + (1 if self.auto_connect_lan_var.get() else 0)
                + (1 if self.auto_connect_var.get() else 0)
            )

            # 切换为 DHCP + 自动 DNS
            for alias, nic, cfg in targets:
                self._log(f"处理 {alias} -> 切换为自动获取IP/DNS")
                try:
                    if getattr(cfg, "DHCPEnabled", None) is False:
                        rc = _first(cfg.EnableDHCP())
                        if rc not in (0, None):
                            self._log(f"EnableDHCP 返回码 {rc} ({alias})")
                    _ = cfg.SetDNSServerSearchOrder()
                except Exception as e:
                    self._log(f"切换为 DHCP 失败：{alias}: {e}")
                self._step()

            # 禁用/启用并尝试续租 DHCP
            for alias, nic, cfg in targets:
                self._log(f"重置 {alias} -> 先禁用再启用")
                try:
                    rc1 = _first(nic.Disable())
                    time.sleep(2)
                    rc2 = _first(nic.Enable())
                    if rc1 not in (0, None):
                        self._log(f"Disable 返回码 {rc1} ({alias})")
                    if rc2 not in (0, None):
                        self._log(f"Enable 返回码 {rc2} ({alias})")
                    try:
                        _ = cfg.ReleaseDHCPLease()
                        _ = cfg.RenewDHCPLease()
                    except Exception:
                        pass
                except Exception as e:
                    self._log(f"重置网卡失败：{alias}: {e}")
                self._step()

            self._log("完成：所有网卡已设置为自动，并已重置连接。")
            if self.auto_connect_lan_var.get():
                self._log("尝试连接最强有线网络…")
                try:
                    self._auto_connect_best_ethernet(targets)
                except Exception as e:
                    self._log(f"有线自动连接失败：{e}")
                self._step()
            if self.auto_connect_var.get():
                self._log("尝试连接最强已保存的无线网络…")
                try:
                    self._auto_connect_best_wifi()
                except Exception as e:
                    self._log(f"自动连接无线失败：{e}")
                self._step()
            self._done(status="完成")
        except Exception as e:
            self._log(f"执行过程中出现错误：{e}")
            self._done(status="错误")

    def _log(self, text: str):
        self.log_queue.put(("log", text))

    def _step(self):
        self.current_step += 1
        if self.total_steps:
            pct = int(self.current_step / self.total_steps * 100)
            self.log_queue.put(("progress", pct))

    def _done(self, status: str):
        self.log_queue.put(("status", status))
        self.log_queue.put(("enable_start", True))

    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self.log_text.insert(tk.END, payload + "\n")
                    self.log_text.see(tk.END)
                elif kind == "progress":
                    self.progress.configure(value=payload)
                elif kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "enable_start":
                    self.btn_start.configure(state=tk.NORMAL)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._drain_queue)

    # ===== Wi-Fi 辅助方法（通过 netsh） =====
    def _run_cmd(self, args):
        # 使用二进制读取，避免 Python 在后台线程用本地编码（如 GBK）直接解码导致异常
        proc = subprocess.run(args, capture_output=True)
        return proc

    def _decode(self, data: bytes) -> str:
        if data is None:
            return ""
        # 优先尝试 UTF-8，再回退到常见的中文编码与宽字符编码，最后兜底 latin-1
        for enc in ("utf-8-sig", "utf-8", "gbk", "cp936", locale.getpreferredencoding(False), "mbcs", "latin-1"):
            try:
                return data.decode(enc, errors="replace")
            except Exception:
                continue
        try:
            return data.decode(errors="replace")
        except Exception:
            return ""

    def _wifi_interfaces(self):
        proc = self._run_cmd(["netsh", "wlan", "show", "interfaces"])
        if proc.returncode != 0:
            self._log("获取 Wi-Fi 接口失败：" + self._decode(proc.stderr).strip())
            return []
        names = []
        out = self._decode(proc.stdout)
        for line in out.splitlines():
            line = line.strip()
            m = re.match(r"(?i)(名称|Name)\s*:\s*(.+)", line)
            if m:
                names.append(m.group(2).strip())
        return names

    def _saved_profiles(self):
        proc = self._run_cmd(["netsh", "wlan", "show", "profiles"])
        if proc.returncode != 0:
            self._log("获取保存的 Wi-Fi 配置失败：" + self._decode(proc.stderr).strip())
            return []
        profiles = []
        out = self._decode(proc.stdout)
        for line in out.splitlines():
            line = line.strip()
            m1 = re.search(r"(?i)All\s+User\s+Profile\s*:\s*(.+)", line)
            m2 = re.search(r"(?i)(所有用户配置文件|当前用户配置文件)\s*:\s*(.+)", line)
            if m1:
                profiles.append(m1.group(1).strip())
            elif m2:
                profiles.append(m2.group(2).strip())
        return profiles

    def _scan_networks(self):
        proc = self._run_cmd(["netsh", "wlan", "show", "networks", "mode=bssid"])
        if proc.returncode != 0:
            self._log("扫描 Wi-Fi 失败：" + self._decode(proc.stderr).strip())
            return {}
        best = {}
        current_ssid = None
        out = self._decode(proc.stdout)
        for line in out.splitlines():
            line = line.strip()
            mssid = re.match(r"(?i)SSID\s*\d+\s*:\s*(.+)", line)
            if mssid:
                ssid = mssid.group(1).strip()
                current_ssid = ssid if ssid else None
                continue
            msig = re.match(r"(?i)(信号|Signal)\s*:\s*(\d+)\s*%", line)
            if msig and current_ssid:
                pct = int(msig.group(2))
                best[current_ssid] = max(best.get(current_ssid, 0), pct)
        return best

    def _auto_connect_best_wifi(self):
        profiles = self._saved_profiles()
        if not profiles:
            self._log("未发现已保存的 Wi-Fi 配置")
            return
        signals = self._scan_networks()
        candidates = [(p, signals.get(p, 0)) for p in profiles if p in signals]
        if not candidates:
            self._log("附近未发现与已保存配置匹配的网络")
            return
        candidates.sort(key=lambda x: x[1], reverse=True)
        target_profile, strength = candidates[0]
        self._log(f"选择：{target_profile}（信号 {strength}%）")

        interfaces = self._wifi_interfaces()
        args = ["netsh", "wlan", "connect", f"name={target_profile}"]
        if interfaces:
            args.append(f"interface={interfaces[0]}")
        proc = self._run_cmd(args)
        out = self._decode(proc.stdout) + ("\n" + self._decode(proc.stderr) if proc.stderr else "")
        self._log(out.strip() or "已发起连接请求")
        time.sleep(3)
        # 确认连接状态
        confirm = self._run_cmd(["netsh", "wlan", "show", "interfaces"])
        connected = False
        current_ssid = None
        confirm_out = self._decode(confirm.stdout)
        for line in confirm_out.splitlines():
            line = line.strip()
            mstate = re.match(r"(?i)(状态|State)\s*:\s*(.+)", line)
            mssid = re.match(r"(?i)SSID\s*:\s*(.+)", line)
            if mstate:
                s = mstate.group(2).strip().lower()
                if "connected" in s or "已连接" in s:
                    connected = True
            if mssid:
                current_ssid = mssid.group(1).strip()
        if connected:
            self._log(f"已连接到：{current_ssid or target_profile}")
        else:
            self._log("连接未确认，请在系统托盘检查 Wi-Fi 状态")

    # ===== 有线（以太网）自动连接 =====
    def _fmt_speed(self, bps: int) -> str:
        try:
            bps = int(bps)
        except Exception:
            return "未知速度"
        if bps >= 1_000_000_000:
            return f"{bps/1_000_000_000:.1f} Gbps"
        if bps >= 1_000_000:
            return f"{bps/1_000_000:.0f} Mbps"
        if bps >= 1_000:
            return f"{bps/1_000:.0f} Kbps"
        return f"{bps} bps"

    def _auto_connect_best_ethernet(self, targets):
        # 选择速度最高的以太网，优先已获得IP（IPEnabled=True）
        cands = []
        for alias, nic, cfg in targets:
            if nic.AdapterTypeID != 0:
                continue
            name = (alias or "").lower()
            if "bluetooth" in name or "蓝牙" in name:
                continue
            speed = int(nic.Speed or 0)
            ipenabled = bool(getattr(cfg, "IPEnabled", False))
            cands.append((alias, nic, cfg, speed, ipenabled))

        if not cands:
            self._log("未发现以太网接口")
            return

        # 排序：先按是否已有IP，其次按速度
        cands.sort(key=lambda x: (x[4], x[3]), reverse=True)
        alias, nic, cfg, speed, ipenabled = cands[0]
        self._log(f"选择有线：{alias}（{self._fmt_speed(speed)}{'，已获得IP' if ipenabled else ''}）")

        try:
            # 确保启用
            _ = _first(nic.Enable())
        except Exception:
            pass

        # 启用 DHCP 并尝试续租
        try:
            _ = cfg.EnableDHCP()
        except Exception:
            pass
        try:
            _ = cfg.ReleaseDHCPLease()
            _ = cfg.RenewDHCPLease()
        except Exception:
            pass

        # 简单确认：重新查询接口是否有IP
        try:
            import wmi  # type: ignore
            c = wmi.WMI()
            cfg2 = next((x for x in c.Win32_NetworkAdapterConfiguration() if x.Index == nic.Index), None)
            if cfg2 and getattr(cfg2, "IPEnabled", False):
                self._log(f"有线连接已启用并获得IP：{alias}")
            else:
                self._log(f"未确认有线连接获得IP：{alias}，请检查网线与交换机端口")
        except Exception:
            pass


def main():
    # 取消阻塞式展示，改为线程触发展示
    elevate_if_needed()

    # 自动安装并导入 PyQt5 与 wmi 依赖
    if not ensure_module("PyQt5", "PyQt5"):
        print("缺少 PyQt5，已尝试使用阿里云镜像安装，请重试运行。")
        return
    ensure_module("wmi", "wmi")
    # 确保 pywin32 存在以提供 pythoncom（COM 初始化）
    ensure_module("pywin32", "pywin32")

    from PyQt5.QtWidgets import (
        QApplication,
        QLabel,
        QMainWindow,
        QProgressBar,
        QVBoxLayout,
        QWidget,
        QHBoxLayout,
        QPlainTextEdit,
        QPushButton,
        QCheckBox,
    )
    from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
    from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QIcon

    class GradientWidget(QWidget):
        def paintEvent(self, event):
            painter = QPainter(self)
            grad = QLinearGradient(0, 0, 0, self.height())
            grad.setColorAt(0, QColor(20, 28, 45))
            grad.setColorAt(1, QColor(9, 13, 20))
            painter.fillRect(self.rect(), grad)

    class Worker(QThread):
        log = pyqtSignal(str)
        progress = pyqtSignal(int)
        status = pyqtSignal(str)
        enable_start = pyqtSignal(bool)

        def __init__(self, auto_wifi: bool = True, auto_lan: bool = True):
            super().__init__()
            self.auto_wifi = auto_wifi
            self.auto_lan = auto_lan
            self.total_steps = 0
            self.current_step = 0

        def _step(self):
            self.current_step += 1
            if self.total_steps:
                pct = int(self.current_step / self.total_steps * 100)
                self.progress.emit(pct)

        def run(self):
            # 在线程中初始化 COM，避免 x_wmi 语法错误（需要在每个线程调用）
            _com_initialized = False
            try:
                import pythoncom  # type: ignore
                pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
                _com_initialized = True
            except Exception as e:
                self.log.emit(f"COM 初始化失败：{e}")

            try:
                import wmi  # type: ignore
            except ImportError:
                self.log.emit("缺少 wmi 依赖。请安装：.venv\\Scripts\\pip install -i https://mirrors.aliyun.com/pypi/simple/ wmi")
                self.status.emit("依赖缺失")
                self.enable_start.emit(True)
                if _com_initialized:
                    try:
                        pythoncom.CoUninitialize()  # type: ignore
                    except Exception:
                        pass
                return

            try:
                c = wmi.WMI()
                cfg_by_index = {cfg.Index: cfg for cfg in c.Win32_NetworkAdapterConfiguration()}
                targets = []
                for nic in c.Win32_NetworkAdapter(PhysicalAdapter=True):
                    if nic.AdapterTypeID not in (0, 9):
                        continue
                    alias = nic.NetConnectionID or nic.Name or f"Index {nic.Index}"
                    if alias and alias.lower() and ("bluetooth" in alias.lower() or "蓝牙" in alias.lower()):
                        continue
                    cfg = cfg_by_index.get(nic.Index)
                    if not cfg:
                        continue
                    targets.append((alias, nic, cfg))

                if not targets:
                    self.log.emit("未发现物理有线/无线网卡")
                    self.status.emit("无网卡")
                    self.enable_start.emit(True)
                    return

                self.log.emit("发现网卡: " + ", ".join([alias for alias, _, _ in targets]))
                self.total_steps = len(targets) * 2 + (1 if self.auto_lan else 0) + (1 if self.auto_wifi else 0)

                # 切换为 DHCP + 自动 DNS
                for alias, nic, cfg in targets:
                    self.log.emit(f"处理 {alias} -> 切换为自动获取IP/DNS")
                    try:
                        if getattr(cfg, "DHCPEnabled", None) is False:
                            rc = _first(cfg.EnableDHCP())
                            if rc not in (0, None):
                                self.log.emit(f"EnableDHCP 返回码 {rc} ({alias})")
                        _ = cfg.SetDNSServerSearchOrder()
                    except Exception as e:
                        self.log.emit(f"切换为 DHCP 失败：{alias}: {e}")
                    self._step()

                # 禁用/启用并尝试续租 DHCP
                for alias, nic, cfg in targets:
                    self.log.emit(f"重置 {alias} -> 先禁用再启用")
                    try:
                        rc1 = _first(nic.Disable())
                        time.sleep(2)
                        rc2 = _first(nic.Enable())
                        if rc1 not in (0, None):
                            self.log.emit(f"Disable 返回码 {rc1} ({alias})")
                        if rc2 not in (0, None):
                            self.log.emit(f"Enable 返回码 {rc2} ({alias})")
                        try:
                            _ = cfg.ReleaseDHCPLease()
                            _ = cfg.RenewDHCPLease()
                        except Exception:
                            pass
                    except Exception as e:
                        self.log.emit(f"重置网卡失败：{alias}: {e}")
                    self._step()

                self.log.emit("完成：所有网卡已设置为自动，并已重置连接。")
                if self.auto_lan:
                    self.log.emit("尝试连接最强有线网络…")
                    try:
                        self._auto_connect_best_ethernet(targets)
                    except Exception as e:
                        self.log.emit(f"有线自动连接失败：{e}")
                    self._step()
                if self.auto_wifi:
                    self.log.emit("尝试连接最强已保存的无线网络…")
                    try:
                        self._auto_connect_best_wifi()
                    except Exception as e:
                        self.log.emit(f"自动连接无线失败：{e}")
                    self._step()
                self.status.emit("完成")
                self.enable_start.emit(True)
            except Exception as e:
                self.log.emit(f"执行过程中出现错误：{e}")
                self.status.emit("错误")
                self.enable_start.emit(True)
            finally:
                if _com_initialized:
                    try:
                        pythoncom.CoUninitialize()  # type: ignore
                    except Exception:
                        pass

        # ===== Wi-Fi 与有线辅助方法 =====
        def _run_cmd(self, args):
            proc = subprocess.run(args, capture_output=True)
            return proc

        def _decode(self, data: bytes) -> str:
            if data is None:
                return ""
            for enc in ("utf-8-sig", "utf-8", "gbk", "cp936", locale.getpreferredencoding(False), "mbcs", "latin-1"):
                try:
                    return data.decode(enc, errors="replace")
                except Exception:
                    continue
            try:
                return data.decode(errors="replace")
            except Exception:
                return ""

        def _wifi_interfaces(self):
            proc = self._run_cmd(["netsh", "wlan", "show", "interfaces"])
            if proc.returncode != 0:
                self.log.emit("获取 Wi-Fi 接口失败：" + self._decode(proc.stderr).strip())
                return []
            names = []
            out = self._decode(proc.stdout)
            for line in out.splitlines():
                m = re.match(r"(?i)(名称|Name)\s*:\s*(.+)", line.strip())
                if m:
                    names.append(m.group(2).strip())
            return names

        def _saved_profiles(self):
            proc = self._run_cmd(["netsh", "wlan", "show", "profiles"])
            if proc.returncode != 0:
                self.log.emit("获取保存的 Wi-Fi 配置失败：" + self._decode(proc.stderr).strip())
                return []
            profiles = []
            out = self._decode(proc.stdout)
            for line in out.splitlines():
                l = line.strip()
                m1 = re.search(r"(?i)All\s+User\s+Profile\s*:\s*(.+)", l)
                m2 = re.search(r"(?i)(所有用户配置文件|当前用户配置文件)\s*:\s*(.+)", l)
                if m1:
                    profiles.append(m1.group(1).strip())
                elif m2:
                    profiles.append(m2.group(2).strip())
            return profiles

        def _scan_networks(self):
            proc = self._run_cmd(["netsh", "wlan", "show", "networks", "mode=bssid"])
            if proc.returncode != 0:
                self.log.emit("扫描 Wi-Fi 失败：" + self._decode(proc.stderr).strip())
                return {}
            best = {}
            current_ssid = None
            out = self._decode(proc.stdout)
            for line in out.splitlines():
                s = line.strip()
                mssid = re.match(r"(?i)SSID\s*\d+\s*:\s*(.+)", s)
                if mssid:
                    ssid = mssid.group(1).strip()
                    current_ssid = ssid if ssid else None
                    continue
                msig = re.match(r"(?i)(信号|Signal)\s*:\s*(\d+)\s*%", s)
                if msig and current_ssid:
                    pct = int(msig.group(2))
                    best[current_ssid] = max(best.get(current_ssid, 0), pct)
            return best

        def _auto_connect_best_wifi(self):
            profiles = self._saved_profiles()
            if not profiles:
                self.log.emit("未发现已保存的 Wi-Fi 配置")
                return
            signals = self._scan_networks()
            candidates = [(p, signals.get(p, 0)) for p in profiles if p in signals]
            if not candidates:
                self.log.emit("附近未发现与已保存配置匹配的网络")
                return
            candidates.sort(key=lambda x: x[1], reverse=True)
            target_profile, strength = candidates[0]
            self.log.emit(f"选择：{target_profile}（信号 {strength}%）")
            interfaces = self._wifi_interfaces()
            args = ["netsh", "wlan", "connect", f"name={target_profile}"]
            if interfaces:
                args.append(f"interface={interfaces[0]}")
            proc = self._run_cmd(args)
            out = self._decode(proc.stdout) + ("\n" + self._decode(proc.stderr) if proc.stderr else "")
            self.log.emit(out.strip() or "已发起连接请求")
            time.sleep(3)
            confirm = self._run_cmd(["netsh", "wlan", "show", "interfaces"])
            connected = False
            current_ssid = None
            confirm_out = self._decode(confirm.stdout)
            for line in confirm_out.splitlines():
                l = line.strip()
                mstate = re.match(r"(?i)(状态|State)\s*:\s*(.+)", l)
                mssid = re.match(r"(?i)SSID\s*:\s*(.+)", l)
                if mstate:
                    s = mstate.group(2).strip().lower()
                    if "connected" in s or "已连接" in s:
                        connected = True
                if mssid:
                    current_ssid = mssid.group(1).strip()
            if connected:
                self.log.emit(f"已连接到：{current_ssid or target_profile}")
            else:
                self.log.emit("连接未确认，请在系统托盘检查 Wi-Fi 状态")

        def _fmt_speed(self, bps: int) -> str:
            try:
                bps = int(bps)
            except Exception:
                return "未知速度"
            if bps >= 1_000_000_000:
                return f"{bps/1_000_000_000:.1f} Gbps"
            if bps >= 1_000_000:
                return f"{bps/1_000_000:.0f} Mbps"
            if bps >= 1_000:
                return f"{bps/1_000:.0f} Kbps"
            return f"{bps} bps"

        def _auto_connect_best_ethernet(self, targets):
            cands = []
            for alias, nic, cfg in targets:
                if nic.AdapterTypeID != 0:
                    continue
                name = (alias or "").lower()
                if "bluetooth" in name or "蓝牙" in name:
                    continue
                speed = int(nic.Speed or 0)
                ipenabled = bool(getattr(cfg, "IPEnabled", False))
                cands.append((alias, nic, cfg, speed, ipenabled))
            if not cands:
                self.log.emit("未发现以太网接口")
                return
            cands.sort(key=lambda x: (x[4], x[3]), reverse=True)
            alias, nic, cfg, speed, ipenabled = cands[0]
            self.log.emit(f"选择有线：{alias}（{self._fmt_speed(speed)}{'，已获得IP' if ipenabled else ''}）")
            try:
                _ = _first(nic.Enable())
            except Exception:
                pass
            try:
                _ = cfg.EnableDHCP()
            except Exception:
                pass
            try:
                _ = cfg.ReleaseDHCPLease()
                _ = cfg.RenewDHCPLease()
            except Exception:
                pass
            try:
                import wmi  # type: ignore
                c = wmi.WMI()
                cfg2 = next((x for x in c.Win32_NetworkAdapterConfiguration() if x.Index == nic.Index), None)
                if cfg2 and getattr(cfg2, "IPEnabled", False):
                    self.log.emit(f"有线连接已启用并获得IP：{alias}")
                else:
                    self.log.emit(f"未确认有线连接获得IP：{alias}，请检查网线与交换机端口")
            except Exception:
                pass

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("网络修复工具")
            self.resize(820, 540)
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            # 无边框窗口
            self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            central = GradientWidget()
            self.setCentralWidget(central)
            vbox = QVBoxLayout(central)
            top = QWidget()
            top_layout = QHBoxLayout(top)
            vbox.addWidget(top)
            self.btn_start = QPushButton("开始修复")
            self.btn_start.setCursor(Qt.PointingHandCursor)
            self.btn_exit = QPushButton("退出")
            self.btn_exit.setCursor(Qt.PointingHandCursor)
            self.auto_wifi = QCheckBox("自动连接最强已保存 Wi-Fi")
            self.auto_wifi.setChecked(True)
            self.auto_lan = QCheckBox("自动连接最强有线")
            self.auto_lan.setChecked(True)
            self.status = QLabel("就绪：点击“开始修复”执行")
            self.status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            top_layout.addWidget(self.btn_start)
            top_layout.addWidget(self.auto_wifi)
            top_layout.addWidget(self.auto_lan)
            top_layout.addWidget(self.btn_exit)
            top_layout.addWidget(self.status)
            self.progress = QProgressBar()
            self.progress.setRange(0, 100)
            vbox.addWidget(self.progress)
            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            vbox.addWidget(self.log, 1)
            self.worker = None
            self.btn_start.clicked.connect(self.on_start)
            self.btn_exit.clicked.connect(self.close)

            # 全局样式：字体白色；日志输出黑底白字；进度条与按钮蓝黑主题
            self.setStyleSheet(
                """
                QWidget { color: #ffffff; }
                QLabel { color: #ffffff; }
                QCheckBox { color: #ffffff; }
                QPushButton {
                    color: #ffffff;
                    background-color: #0d6efd;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: #0b5ed7; }
                QPushButton:disabled { background-color: #3d4a61; color: #bbbbbb; }
                QProgressBar {
                    color: #ffffff;
                    background-color: #1d2538;
                    border: 1px solid #2b3551;
                    border-radius: 4px;
                    text-align: center;
                }
                QProgressBar::chunk { background-color: #0d6efd; }
                QPlainTextEdit {
                    background-color: #000000;
                    color: #ffffff;
                    border: 1px solid #2b3551;
                    selection-background-color: #0d6efd;
                    selection-color: #ffffff;
                }
                """
            )

            # 允许通过拖动窗口任意位置移动（无边框下的友好性）
            self._dragPos = None

        def on_show_splash(self, image: str, url: str):
            try:
                win = FullScreenImageWindow(image, url)
                if not hasattr(self, "_splash_refs"):
                    self._splash_refs = []
                self._splash_refs.append(win)
                win.show()
            except Exception as e:
                self.append_log(f"展示引导图失败：{e}")

        def append_log(self, text: str):
            self.log.appendPlainText(text)
            self.log.moveCursor(self.log.textCursor().End)

        def on_start(self):
            if self.worker and self.worker.isRunning():
                return
            self.progress.setValue(0)
            self.status.setText("执行中…")
            self.btn_start.setEnabled(False)
            self.append_log("开始执行网络修复…")
            self.worker = Worker(auto_wifi=self.auto_wifi.isChecked(), auto_lan=self.auto_lan.isChecked())
            self.worker.log.connect(self.append_log)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.status.connect(self.status.setText)
            self.worker.enable_start.connect(lambda enabled: self.btn_start.setEnabled(enabled))
            self.worker.start()

    

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    QTimer.singleShot(500, lambda: show_windows_toast(
        title="网络修复工具",
        message="点击打开官网",
        duration=5,
        icon="https://youke1.picui.cn/s1/2025/11/10/691168572c066.png",
        url="http://leyon.top/"
    ))
    app.exec_()


if __name__ == "__main__":
    
    main()