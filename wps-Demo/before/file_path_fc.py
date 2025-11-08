import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os


def fc_path_get():
    """
    基于tkinter实现弹出一个弹窗，拖动一个文件到指定区域，然后返回该文件的路径
    
    Returns:
        str: 拖拽文件的完整路径，如果用户取消或未选择文件则返回None
    """
    
    # 用于存储文件路径的变量
    file_path = None
    
    # 创建主窗口
    root = TkinterDnD.Tk()
    root.title("文件拖拽选择器")
    root.geometry("500x300")
    root.resizable(True, True)
    
    # 设置窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (500 // 2)
    y = (root.winfo_screenheight() // 2) - (300 // 2)
    root.geometry(f"500x300+{x}+{y}")
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题标签
    title_label = ttk.Label(main_frame, text="文件拖拽选择器", font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # 说明标签
    instruction_label = ttk.Label(main_frame, text="请将文件拖拽到下方区域", font=("Arial", 10))
    instruction_label.pack(pady=(0, 10))
    
    # 创建拖拽区域
    drop_frame = tk.Frame(main_frame, bg="#f0f0f0", relief="ridge", bd=2)
    drop_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
    
    # 拖拽区域标签
    drop_label = tk.Label(drop_frame, text="拖拽文件到此处\n或点击选择文件", 
                         bg="#f0f0f0", font=("Arial", 12), fg="#666666")
    drop_label.pack(expand=True)
    
    # 显示选中文件路径的标签
    path_label = ttk.Label(main_frame, text="", font=("Arial", 9), foreground="blue")
    path_label.pack(pady=(0, 10), fill=tk.X)
    
    # 按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X)
    
    def on_drop(event):
        """处理文件拖拽事件"""
        nonlocal file_path
        files = root.tk.splitlist(event.data)
        if files:
            dropped_file = files[0]  # 只取第一个文件
            if os.path.isfile(dropped_file):
                file_path = dropped_file
                # 显示文件路径（如果路径太长，只显示文件名和部分路径）
                display_path = file_path
                if len(display_path) > 60:
                    display_path = "..." + display_path[-57:]
                path_label.config(text=f"已选择: {display_path}")
                drop_label.config(text=f"已选择文件:\n{os.path.basename(file_path)}", fg="green")
            else:
                messagebox.showwarning("警告", "请拖拽一个有效的文件！")
    
    def on_file_select():
        """通过文件对话框选择文件"""
        nonlocal file_path
        from tkinter import filedialog
        selected_file = filedialog.askopenfilename(
            title="选择文件",
            filetypes=[("所有文件", "*.*")]
        )
        if selected_file:
            file_path = selected_file
            # 显示文件路径
            display_path = file_path
            if len(display_path) > 60:
                display_path = "..." + display_path[-57:]
            path_label.config(text=f"已选择: {display_path}")
            drop_label.config(text=f"已选择文件:\n{os.path.basename(file_path)}", fg="green")
    
    def on_confirm():
        """确认选择"""
        if file_path:
            root.quit()
        else:
            messagebox.showwarning("警告", "请先选择一个文件！")
    
    def on_cancel():
        """取消选择"""
        nonlocal file_path
        file_path = None
        root.quit()
    
    # 绑定拖拽事件
    drop_frame.drop_target_register(DND_FILES)
    drop_frame.dnd_bind('<<Drop>>', on_drop)
    
    # 绑定点击事件
    drop_frame.bind("<Button-1>", lambda e: on_file_select())
    drop_label.bind("<Button-1>", lambda e: on_file_select())
    
    # 创建按钮
    ttk.Button(button_frame, text="浏览文件", command=on_file_select).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Button(button_frame, text="确定", command=on_confirm).pack(side=tk.RIGHT, padx=(10, 0))
    ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.RIGHT)
    
    # 设置窗口关闭事件
    def on_closing():
        nonlocal file_path
        file_path = None
        root.quit()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()
    
    # 销毁窗口
    root.destroy()
    
    return file_path


# 测试函数（可选）
if __name__ == "__main__":
    print("启动文件选择器...")
    selected_path = fc_path_get()
    if selected_path:
        print(f"选择的文件路径: {selected_path}")
    else:
        print("未选择文件或用户取消操作")