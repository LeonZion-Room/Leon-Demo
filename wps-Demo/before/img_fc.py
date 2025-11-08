import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import os
import io


class ImagePreviewWindow:
    """图片分割预览窗口"""
    
    def __init__(self, parent, image_path, split_count):
        self.parent = parent
        self.image_path = image_path
        self.split_count = split_count
        self.current_page = 0
        self.segments = []
        self.confirmed = False
        
        # 创建预览窗口
        self.window = tk.Toplevel(parent)
        self.window.title("预览分割效果")
        self.window.geometry("800x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 居中显示
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (800 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
        
        self.setup_ui()
        self.load_image_segments()
        self.show_current_page()
        
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="预览分割效果", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 信息标签
        info_text = f"图片将被分割为 {self.split_count} 页，请预览每页效果"
        info_label = ttk.Label(main_frame, text=info_text, font=("Arial", 11))
        info_label.pack(pady=(0, 15))
        
        # 图片显示区域
        self.image_frame = ttk.Frame(main_frame, relief="ridge", borderwidth=2)
        self.image_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 图片标签
        self.image_label = ttk.Label(self.image_frame, text="正在加载...", font=("Arial", 12))
        self.image_label.pack(expand=True)
        
        # 控制区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 翻页按钮
        self.prev_btn = ttk.Button(control_frame, text="◀ 上一页", command=self.prev_page)
        self.prev_btn.pack(side=tk.LEFT)
        
        # 页码显示
        self.page_label = ttk.Label(control_frame, text="", font=("Arial", 12, "bold"))
        self.page_label.pack(side=tk.LEFT, padx=(20, 20))
        
        self.next_btn = ttk.Button(control_frame, text="下一页 ▶", command=self.next_page)
        self.next_btn.pack(side=tk.LEFT)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 确认和取消按钮
        ttk.Button(button_frame, text="确认保存PDF", command=self.confirm_save).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT)
        
        # 绑定键盘事件
        self.window.bind('<Left>', lambda e: self.prev_page())
        self.window.bind('<Right>', lambda e: self.next_page())
        self.window.bind('<Return>', lambda e: self.confirm_save())
        self.window.bind('<Escape>', lambda e: self.cancel())
        
        # 设置焦点以接收键盘事件
        self.window.focus_set()
        
    def load_image_segments(self):
        """加载并分割图片"""
        try:
            with Image.open(self.image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                width, height = img.size
                segment_height = height // self.split_count
                
                # 分割图片
                for i in range(self.split_count):
                    top = i * segment_height
                    bottom = min((i + 1) * segment_height, height)
                    
                    # 如果是最后一段，包含剩余的像素
                    if i == self.split_count - 1:
                        bottom = height
                    
                    # 分割图片
                    segment = img.crop((0, top, width, bottom))
                    self.segments.append(segment.copy())
                    
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败：{str(e)}")
            self.cancel()
            
    def show_current_page(self):
        """显示当前页"""
        if not self.segments:
            return
            
        try:
            # 获取当前段
            segment = self.segments[self.current_page]
            
            # 计算显示尺寸（保持宽高比，适应显示区域）
            display_width = 760  # 预留边距
            display_height = 400  # 预留边距
            
            # 计算缩放比例
            scale_x = display_width / segment.width
            scale_y = display_height / segment.height
            scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
            
            # 计算新尺寸
            new_width = int(segment.width * scale)
            new_height = int(segment.height * scale)
            
            # 调整图片大小
            resized_segment = segment.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为Tkinter可显示的格式
            photo = ImageTk.PhotoImage(resized_segment)
            
            # 更新图片标签
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # 保持引用
            
            # 更新页码显示
            self.page_label.config(text=f"第 {self.current_page + 1} 页 / 共 {self.split_count} 页")
            
            # 更新按钮状态
            self.prev_btn.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.current_page < self.split_count - 1 else tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示图片失败：{str(e)}")
            
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_page()
            
    def next_page(self):
        """下一页"""
        if self.current_page < self.split_count - 1:
            self.current_page += 1
            self.show_current_page()
            
    def confirm_save(self):
        """确认保存"""
        self.confirmed = True
        self.window.destroy()
        
    def cancel(self):
        """取消操作"""
        self.confirmed = False
        self.window.destroy()
        
    def show_modal(self):
        """显示模态窗口并返回用户选择"""
        self.window.wait_window()
        return self.confirmed


def img_edit():
    """
    长图编辑功能：将图片纵向分割为指定份数，输出为按顺序拼接的PDF
    
    功能说明：
    1. 弹出GUI界面让用户选择图片文件
    2. 用户输入分割份数
    3. 将图片纵向等分为指定份数
    4. 将分割后的图片按顺序拼接成PDF
    5. 输出到相同目录下，文件名为"源文件名(编辑后).pdf"
    
    Returns:
        str: 输出PDF文件的路径，如果操作失败则返回None
    """
    
    # 用于存储选择的文件路径和分割份数
    selected_file = None
    split_count = None
    result_path = None
    
    # 创建主窗口
    root = TkinterDnD.Tk()
    root.title("长图编辑器")
    root.geometry("600x400")
    root.resizable(True, True)
    
    # 设置窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (600 // 2)
    y = (root.winfo_screenheight() // 2) - (400 // 2)
    root.geometry(f"600x400+{x}+{y}")
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题标签
    title_label = ttk.Label(main_frame, text="长图编辑器", font=("Arial", 18, "bold"))
    title_label.pack(pady=(0, 20))
    
    # 说明标签
    instruction_label = ttk.Label(main_frame, text="请选择要编辑的图片文件，然后设置分割份数", font=("Arial", 11))
    instruction_label.pack(pady=(0, 15))
    
    # 文件选择区域
    file_frame = ttk.LabelFrame(main_frame, text="选择图片文件", padding="10")
    file_frame.pack(fill=tk.X, pady=(0, 15))
    
    # 创建拖拽区域
    drop_frame = tk.Frame(file_frame, bg="#f0f0f0", relief="ridge", bd=2, height=100)
    drop_frame.pack(fill=tk.X, pady=(0, 10))
    drop_frame.pack_propagate(False)
    
    # 拖拽区域标签
    drop_label = tk.Label(drop_frame, text="拖拽图片文件到此处\n或点击下方按钮选择文件", 
                         bg="#f0f0f0", font=("Arial", 10), fg="#666666")
    drop_label.pack(expand=True)
    
    # 显示选中文件路径的标签
    file_path_label = ttk.Label(file_frame, text="", font=("Arial", 9), foreground="blue")
    file_path_label.pack(pady=(5, 10), fill=tk.X)
    
    # 文件选择按钮
    def select_file():
        nonlocal selected_file
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            selected_file = file_path
            # 显示文件路径
            display_path = file_path
            if len(display_path) > 70:
                display_path = "..." + display_path[-67:]
            file_path_label.config(text=f"已选择: {display_path}")
            drop_label.config(text=f"已选择文件:\n{os.path.basename(file_path)}", fg="green")
    
    def on_drop(event):
        """处理文件拖拽事件"""
        nonlocal selected_file
        files = root.tk.splitlist(event.data)
        if files:
            dropped_file = files[0]  # 只取第一个文件
            if os.path.isfile(dropped_file):
                # 检查是否为图片文件
                valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
                if dropped_file.lower().endswith(valid_extensions):
                    selected_file = dropped_file
                    # 显示文件路径
                    display_path = dropped_file
                    if len(display_path) > 70:
                        display_path = "..." + display_path[-67:]
                    file_path_label.config(text=f"已选择: {display_path}")
                    drop_label.config(text=f"已选择文件:\n{os.path.basename(dropped_file)}", fg="green")
                else:
                    messagebox.showwarning("警告", "请拖拽一个有效的图片文件！")
            else:
                messagebox.showwarning("警告", "请拖拽一个有效的文件！")
    
    # 绑定拖拽事件
    drop_frame.drop_target_register(DND_FILES)
    drop_frame.dnd_bind('<<Drop>>', on_drop)
    drop_frame.bind("<Button-1>", lambda e: select_file())
    drop_label.bind("<Button-1>", lambda e: select_file())
    
    select_file_btn = ttk.Button(file_frame, text="浏览文件", command=select_file)
    select_file_btn.pack()
    
    # 分割设置区域
    split_frame = ttk.LabelFrame(main_frame, text="分割设置", padding="10")
    split_frame.pack(fill=tk.X, pady=(0, 20))
    
    # 分割份数输入
    split_label = ttk.Label(split_frame, text="请输入分割份数（2-20）：", font=("Arial", 11))
    split_label.pack(anchor=tk.W, pady=(0, 5))
    
    split_var = tk.StringVar(value="2")
    split_entry = ttk.Entry(split_frame, textvariable=split_var, font=("Arial", 11), width=10)
    split_entry.pack(anchor=tk.W, pady=(0, 10))
    
    # 预览信息
    preview_label = ttk.Label(split_frame, text="", font=("Arial", 9), foreground="gray")
    preview_label.pack(anchor=tk.W)
    
    def update_preview():
        """更新预览信息"""
        if selected_file and split_var.get().isdigit():
            try:
                count = int(split_var.get())
                if 2 <= count <= 20:
                    with Image.open(selected_file) as img:
                        width, height = img.size
                        segment_height = height // count
                        preview_label.config(
                            text=f"图片尺寸: {width}×{height}，分割后每段高度: {segment_height}px",
                            foreground="green"
                        )
                else:
                    preview_label.config(text="分割份数必须在2-20之间", foreground="red")
            except Exception as e:
                preview_label.config(text=f"无法读取图片: {str(e)}", foreground="red")
        else:
            preview_label.config(text="", foreground="gray")
    
    # 绑定输入框变化事件
    split_var.trace('w', lambda *args: update_preview())
    
    # 按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    def process_image():
        """处理图片分割和PDF生成"""
        nonlocal result_path
        
        # 验证输入
        if not selected_file:
            messagebox.showwarning("警告", "请先选择一个图片文件！")
            return
        
        if not split_var.get().isdigit():
            messagebox.showwarning("警告", "请输入有效的分割份数！")
            return
        
        count = int(split_var.get())
        if not (2 <= count <= 20):
            messagebox.showwarning("警告", "分割份数必须在2-20之间！")
            return
        
        try:
            # 显示预览窗口
            preview_window = ImagePreviewWindow(root, selected_file, count)
            confirmed = preview_window.show_modal()
            
            if not confirmed:
                # 用户取消了预览
                return
            
            # 用户确认后，显示进度窗口并生成PDF
            progress_window = tk.Toplevel(root)
            progress_window.title("生成PDF中...")
            progress_window.geometry("300x100")
            progress_window.transient(root)
            progress_window.grab_set()
            
            # 居中显示进度窗口
            progress_window.update_idletasks()
            x = root.winfo_x() + (root.winfo_width() // 2) - (300 // 2)
            y = root.winfo_y() + (root.winfo_height() // 2) - (100 // 2)
            progress_window.geometry(f"300x100+{x}+{y}")
            
            progress_label = ttk.Label(progress_window, text="正在生成PDF文件，请稍候...", font=("Arial", 11))
            progress_label.pack(expand=True)
            
            progress_window.update()
            
            # 执行图片分割和PDF生成
            result_path = split_image_to_pdf(selected_file, count)
            
            # 关闭进度窗口
            progress_window.destroy()
            
            if result_path:
                messagebox.showinfo("成功", f"PDF生成完成！\n输出文件：{os.path.basename(result_path)}")
                root.quit()
            else:
                messagebox.showerror("错误", "PDF生成失败，请检查文件格式和权限！")
                
        except Exception as e:
            # 关闭进度窗口
            if 'progress_window' in locals():
                progress_window.destroy()
            messagebox.showerror("错误", f"处理过程中出现错误：{str(e)}")
    
    def cancel_operation():
        """取消操作"""
        nonlocal result_path
        result_path = None
        root.quit()
    
    # 创建按钮
    ttk.Button(button_frame, text="预览分割效果", command=process_image).pack(side=tk.RIGHT, padx=(10, 0))
    ttk.Button(button_frame, text="取消", command=cancel_operation).pack(side=tk.RIGHT)
    
    # 设置窗口关闭事件
    def on_closing():
        nonlocal result_path
        result_path = None
        root.quit()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()
    
    # 销毁窗口
    root.destroy()
    
    return result_path


def split_image_to_pdf(image_path, split_count):
    """
    将图片纵向分割为指定份数，并生成PDF
    
    Args:
        image_path (str): 输入图片文件的路径
        split_count (int): 分割份数
        
    Returns:
        str: 输出PDF文件的路径，如果处理失败则返回None
    """
    
    try:
        # 检查输入文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"输入文件不存在: {image_path}")
        
        # 生成输出文件路径
        input_dir = os.path.dirname(image_path)
        input_filename = os.path.basename(image_path)
        name_without_ext = os.path.splitext(input_filename)[0]
        output_pdf_path = os.path.join(input_dir, f"{name_without_ext}(编辑后).pdf")
        
        print(f"开始处理图片: {image_path}")
        print(f"分割份数: {split_count}")
        print(f"输出文件: {output_pdf_path}")
        
        # 打开图片
        with Image.open(image_path) as img:
            # 转换为RGB模式（确保兼容性）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            width, height = img.size
            segment_height = height // split_count
            
            print(f"图片尺寸: {width}×{height}")
            print(f"每段高度: {segment_height}")
            
            # 创建PDF
            c = canvas.Canvas(output_pdf_path, pagesize=A4)
            
            # 分割图片并添加到PDF
            for i in range(split_count):
                print(f"正在处理第 {i + 1}/{split_count} 段...")
                
                # 计算分割区域
                top = i * segment_height
                bottom = min((i + 1) * segment_height, height)
                
                # 如果是最后一段，包含剩余的像素
                if i == split_count - 1:
                    bottom = height
                
                # 分割图片
                segment = img.crop((0, top, width, bottom))
                
                # 将图片段保存到内存中
                img_buffer = io.BytesIO()
                segment.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # 计算在PDF页面中的尺寸
                page_width, page_height = A4
                
                # 计算缩放比例，保持宽高比
                scale_x = (page_width - 40) / width  # 留20点边距
                scale_y = (page_height - 40) / segment.height  # 留20点边距
                scale = min(scale_x, scale_y)
                
                # 计算实际尺寸
                img_width = width * scale
                img_height = segment.height * scale
                
                # 计算居中位置
                x = (page_width - img_width) / 2
                y = (page_height - img_height) / 2
                
                # 添加图片到PDF
                c.drawImage(ImageReader(img_buffer), x, y, width=img_width, height=img_height)
                
                # 添加页码
                c.setFont("Helvetica", 10)
                c.drawString(page_width - 50, 20, f"{i + 1}/{split_count}")
                
                # 如果不是最后一页，添加新页面
                if i < split_count - 1:
                    c.showPage()
                
                # 清理内存
                img_buffer.close()
            
            # 保存PDF
            c.save()
            
            print(f"✅ 处理完成: {output_pdf_path}")
            return output_pdf_path
            
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        return None

