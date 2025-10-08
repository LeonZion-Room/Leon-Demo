import tkinter as tk
from tkinter import ttk
import webbrowser

def show_lz_window():
    """
    显示LZ-Studio窗口，包含图片和三个按钮
    """
    # 创建主窗口
    root = tk.Tk()
    root.overrideredirect(True) # 隐藏标题栏
    root.title("LZ-Studio")
    root.geometry("600x400")
    root.resizable(False, False)
    
    # 设置窗口背景色为深色主题
    root.configure(bg='#1E1E1E')
    
    # 设置窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (600 // 2)
    y = (root.winfo_screenheight() // 2) - (400 // 2)
    root.geometry(f"600x410+{x}+{y}")
    
    # 创建主容器框架，深色主题
    main_frame = tk.Frame(root, bg='#1E1E1E', padx=3, pady=3)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 创建上方大的深色区域（图片区域）
    image_frame = tk.Frame(main_frame, bg='#2D2D30', height=340, relief='flat', bd=0)
    image_frame.pack(fill=tk.X, pady=(0, 5))
    image_frame.pack_propagate(False)
    
    # 定义图片链接点击函数
    def open_image_link():
        """打开指定的图片链接"""
        # 这里可以设置您想要的具体链接
        image_link_url = "https://www.example.com"  # 请替换为您想要的链接
        webbrowser.open(image_link_url)
    
    # 在深色区域中添加内容
    content_frame = tk.Frame(image_frame, bg='#2D2D30', cursor='hand2')
    content_frame.place(relx=0.5, rely=0.5, anchor='center')
    
    # 绑定点击事件到整个内容区域
    content_frame.bind("<Button-1>", lambda e: open_image_link())
    
    # 显示文字内容（可点击）
    title_label = tk.Label(
        content_frame,
        text="LZ",
        font=("Microsoft YaHei UI", 48, "bold"),
        fg="#E0E0E0",
        bg='#2D2D30',
        cursor='hand2'
    )
    title_label.pack()
    title_label.bind("<Button-1>", lambda e: open_image_link())
    
    subtitle_label = tk.Label(
        content_frame,
        text="Studio",
        font=("Microsoft YaHei UI", 34),
        fg="#B0B0B0",
        bg='#2D2D30',
        cursor='hand2'
    )
    subtitle_label.pack()
    subtitle_label.bind("<Button-1>", lambda e: open_image_link())
    
    # 添加点击提示
    click_hint_label = tk.Label(
        content_frame,
        text="-> 点击访问网站 <-",
        font=("Microsoft YaHei UI", 30),
        fg="#808080",
        bg='#2D2D30',
        cursor='hand2'
    )
    click_hint_label.pack(pady=(5, 0))
    click_hint_label.bind("<Button-1>", lambda e: open_image_link())
    
    # 添加装饰性元素
    decoration_frame = tk.Frame(content_frame, bg='#2D2D30')
    decoration_frame.pack(pady=15)
    
    # 创建三个深色主题装饰性圆点
    for i, color in enumerate(['#FF6B6B', '#4ECDC4', '#45B7D1']):  # 深色主题配色
        dot_canvas = tk.Canvas(decoration_frame, width=20, height=20, bg='#2D2D30', highlightthickness=0)
        dot_canvas.pack(side=tk.LEFT, padx=5)
        dot_canvas.create_oval(2, 2, 18, 18, fill=color, outline="")
    
    # 创建倒计时提示区域，深色主题
    countdown_frame = tk.Frame(main_frame, bg='#1E1E1E')
    countdown_frame.pack(fill=tk.X, pady=(0, 1))
    
    countdown_label = tk.Label(
        countdown_frame,
        text="窗口将在 5 秒后自动关闭",
        font=("Microsoft YaHei UI", 20, "bold"),
        fg="#B0B0B0",
        bg='#1E1E1E'
    )
    countdown_label.pack()
    
    # 创建下方按钮区域，深色主题
    button_frame = tk.Frame(main_frame, bg='#1E1E1E')
    button_frame.pack(fill=tk.X, pady=1)
    
    # 按钮样式配置，进一步减少高度使布局更紧凑
    button_style = {
        'width': 10,
        'height': 1,
        'font': ('Arial', 10, 'bold'),
        'relief': 'flat',
        'bd': 0,
        'cursor': 'hand2'
    }
    
    # 倒计时变量
    countdown_seconds = 5
    
    def update_countdown():
        """更新倒计时显示"""
        nonlocal countdown_seconds
        if countdown_seconds > 0:
            countdown_label.config(text=f"窗口将在 {countdown_seconds} 秒后自动关闭")
            countdown_seconds -= 1
            root.after(1000, update_countdown)  # 1秒后再次调用
        else:
            exit_application()
    
    def open_official_website():
        """打开LZ-Studio官网"""
        # 这里可以替换为实际的官网地址
        webbrowser.open("https://www.example.com/lz-studio")
    
    def open_contact_info():
        """打开联系方式页面"""
        # 这里可以替换为实际的联系方式页面
        webbrowser.open("https://www.example.com/contact")
    
    def exit_application():
        """退出应用程序"""
        root.quit()
        root.destroy()
    
    # 创建按钮容器，使用深色背景
    button_container = tk.Frame(button_frame, bg='#1E1E1E')
    button_container.pack(expand=True, fill=tk.X)

    
    # 设置窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", exit_application)
    
    # 启动倒计时
    root.after(1000, update_countdown)  # 1秒后开始倒计时
    
    # 启动主循环
    root.mainloop()

# 如果直接运行此文件，则显示窗口
if __name__ == "__main__":
    show_lz_window()