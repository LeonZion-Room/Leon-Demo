import sys
import os
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def has_subdir(path: Path) -> bool:
    try:
        for c in path.iterdir():
            if c.is_dir():
                return True
    except Exception:
        pass
    return False


class DirCheckApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.base_dir = get_base_dir()
        self.excluded: set[str] = set()
        self.loaded_nodes: set[str] = set()

        self.stat_total = tk.IntVar(value=0)
        self.stat_excluded = tk.IntVar(value=0)
        self.stat_included = tk.IntVar(value=0)
        self.progress_text = tk.StringVar(value="")

        self.progress_total = 0
        self.progress_written = 0
        self.scanning = False

        self._build_ui()
        self._populate_root()
        self._estimate_in_background()

    # UI 构建
    def _build_ui(self):
        self.root.title("DirCheck - Tkinter")
        self.root.geometry("980x600")
        self.root.minsize(760, 480)

        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=12, pady=8)
        ttk.Label(top, text=f"程序所在目录：{self.base_dir}").pack(anchor=tk.W)

        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.Frame(body)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=12)

        # TreeView
        self.tree = ttk.Treeview(left, show="tree")
        yscroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.LEFT, fill=tk.Y)

        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<space>", self._on_space_toggle)

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="屏蔽/取消屏蔽该目录", command=self._toggle_selected)

        # 右侧统计与控制
        grp = ttk.LabelFrame(right, text="屏蔽情况与生成")
        grp.pack(fill=tk.Y, padx=4, pady=4)

        row1 = ttk.Frame(grp)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="总文件：").pack(side=tk.LEFT)
        ttk.Label(row1, textvariable=self.stat_total).pack(side=tk.LEFT)

        row2 = ttk.Frame(grp)
        row2.pack(fill=tk.X, pady=4)
        ttk.Label(row2, text="已屏蔽：").pack(side=tk.LEFT)
        ttk.Label(row2, textvariable=self.stat_excluded).pack(side=tk.LEFT)

        row3 = ttk.Frame(grp)
        row3.pack(fill=tk.X, pady=4)
        ttk.Label(row3, text="将写入：").pack(side=tk.LEFT)
        ttk.Label(row3, textvariable=self.stat_included).pack(side=tk.LEFT)

        self.pb = ttk.Progressbar(grp, mode="determinate", length=260)
        self.pb.pack(fill=tk.X, pady=8)

        ttk.Label(grp, textvariable=self.progress_text, wraplength=260, justify=tk.LEFT).pack(fill=tk.X)

        btns = ttk.Frame(grp)
        btns.pack(fill=tk.X, pady=8)
        self.btn_generate = ttk.Button(btns, text="生成 path.txt", command=self._start_generate)
        self.btn_generate.pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="清除屏蔽", command=self._clear_exclusions).pack(fill=tk.X, pady=2)
        ttk.Button(btns, text="刷新估算", command=self._estimate_in_background).pack(fill=tk.X, pady=2)

        hint = ttk.Label(right, text="提示：右键目录可屏蔽/取消；选中后按空格也可切换。", wraplength=260, justify=tk.LEFT)
        hint.pack(fill=tk.X, pady=6)

    def _label_text(self, path: Path) -> str:
        full = str(path.resolve())
        prefix = "🚫" if full in self.excluded else "📁"
        return f"{prefix} {path.name}"

    def _insert_node(self, parent: str, path: Path):
        iid = str(path.resolve())
        text = self._label_text(path)
        # 避免重复插入
        if iid in self.tree.get_children(parent):
            return
        self.tree.insert(parent, "end", iid=iid, text=text)
        if has_subdir(path):
            # 放一个占位子节点以支持懒加载
            self.tree.insert(iid, "end", iid=f"{iid}::__placeholder__", text="...")

    def _populate_root(self):
        for p in self.base_dir.iterdir():
            try:
                if p.is_dir():
                    self._insert_node("", p)
            except Exception:
                continue

    def _populate_children(self, iid: str):
        if iid in self.loaded_nodes:
            return
        path = Path(iid)
        # 清掉占位符
        for child in self.tree.get_children(iid):
            if child.endswith("::__placeholder__"):
                self.tree.delete(child)
        try:
            for c in path.iterdir():
                if c.is_dir():
                    self._insert_node(iid, c)
        except Exception:
            pass
        self.loaded_nodes.add(iid)

    # 事件处理
    def _on_open(self, _):
        iid = self.tree.focus()
        if iid:
            self._populate_children(iid)

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self.tree.focus(row)
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()

    def _on_space_toggle(self, _):
        self._toggle_selected()

    def _toggle_selected(self):
        iid = self.tree.focus()
        if not iid:
            return
        p = Path(iid)
        full = str(p.resolve())
        if full in self.excluded:
            self.excluded.remove(full)
        else:
            self.excluded.add(full)
        # 更新当前节点文本
        self.tree.item(iid, text=self._label_text(p))
        # 估算刷新
        self._estimate_in_background()

    def _clear_exclusions(self):
        self.excluded.clear()
        # 更新所有已加载节点的前缀
        def refresh_all(parent=""):
            for iid in self.tree.get_children(parent):
                if iid.endswith("::__placeholder__"):
                    continue
                p = Path(iid)
                self.tree.item(iid, text=self._label_text(p))
                refresh_all(iid)
        refresh_all("")
        self._estimate_in_background()

    # 统计估算
    def _estimate_in_background(self):
        def worker():
            total, excluded, included = 0, 0, 0
            base = self.base_dir
            excluded_dirs = [Path(x) for x in self.excluded]

            def should_skip(dirpath: Path) -> bool:
                for ex in excluded_dirs:
                    if is_under(dirpath, ex):
                        return True
                return False

            for dirpath, dirnames, filenames in os.walk(base, topdown=True):
                current = Path(dirpath)
                if should_skip(current):
                    excluded += sum(1 for _ in filenames)
                    dirnames[:] = []
                    continue
                for name in filenames:
                    if name == "path.txt" and current == base:
                        continue
                    total += 1
            included = total - excluded
            self.root.after(0, lambda: self._update_stats(total, excluded, included))

        threading.Thread(target=worker, daemon=True).start()

    def _update_stats(self, total: int, excluded: int, included: int):
        self.stat_total.set(total)
        self.stat_excluded.set(excluded)
        self.stat_included.set(included)
        ratio = (excluded / total) if total else 0.0
        self.progress_text.set(f"屏蔽比例：{round(ratio * 100, 2)}%")

    # 生成 path.txt
    def _start_generate(self):
        if self.scanning:
            return
        self.scanning = True
        self.btn_generate.configure(state=tk.DISABLED)
        self.progress_text.set("正在预扫描以确定总数...")
        self.pb.configure(value=0, maximum=100)
        threading.Thread(target=self._generate_worker, daemon=True).start()

    def _compute_included_total(self, base: Path, excluded_dirs: list[Path]) -> int:
        def should_skip(dirpath: Path) -> bool:
            for ex in excluded_dirs:
                if is_under(dirpath, ex):
                    return True
            return False
        count = 0
        for dirpath, dirnames, filenames in os.walk(base, topdown=True):
            current = Path(dirpath)
            if should_skip(current):
                dirnames[:] = []
                continue
            for name in filenames:
                if name == "path.txt" and current == base:
                    continue
                count += 1
        return count

    def _generate_worker(self):
        base = self.base_dir
        excluded_dirs = [Path(x) for x in self.excluded]
        out_file = base / "path.txt"

        total = self._compute_included_total(base, excluded_dirs)
        self.progress_total = total
        self.progress_written = 0
        self.root.after(0, lambda: (self.pb.configure(maximum=max(1, total), value=0)))

        try:
            with out_file.open("w", encoding="utf-8", newline="\n") as f:
                def should_skip(dirpath: Path) -> bool:
                    for ex in excluded_dirs:
                        if is_under(dirpath, ex):
                            return True
                    return False

                for dirpath, dirnames, filenames in os.walk(base, topdown=True):
                    current = Path(dirpath)
                    if should_skip(current):
                        dirnames[:] = []
                        continue
                    for name in filenames:
                        if name == "path.txt" and current == base:
                            continue
                        fp = current / name
                        try:
                            f.write(str(fp.resolve()) + "\n")
                        except Exception:
                            continue
                        self.progress_written += 1
                        written = self.progress_written
                        total_local = self.progress_total
                        self.root.after(0, lambda w=written, t=total_local: (
                            self.pb.configure(value=w),
                            self.progress_text.set(f"写入: {w} / {t} ({int((w/t)*100) if t else 0}%) -> {out_file}")
                        ))
            # 完成
            self.root.after(0, lambda: (
                self.btn_generate.configure(state=tk.NORMAL),
                self.progress_text.set(f"完成，共写入 {self.progress_written} 个文件到: {out_file}")
            ))
        except Exception as e:
            self.root.after(0, lambda: (
                self.btn_generate.configure(state=tk.NORMAL),
                self.progress_text.set(f"发生错误: {e}")
            ))
        finally:
            self.scanning = False


def main():
    root = tk.Tk()
    app = DirCheckApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()