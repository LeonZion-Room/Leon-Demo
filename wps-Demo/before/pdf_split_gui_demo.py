#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF拆分GUI示例程序

这是一个完整的GUI应用程序，演示如何使用pdf_fc.py中的PDF拆分功能。
用户可以通过图形界面选择PDF文件并进行拆分操作。

作者: AI Assistant
日期: 2024
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from pdf_fc import pdf_split


class PDFSplitGUIDemo:
    """PDF拆分GUI演示程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PDF拆分工具 - GUI演示")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置窗口居中
        self.center_window()
        
        # 当前选择的PDF文件
        self.selected_pdf = None
        
        # 创建界面
        self.create_widgets()
        
        # 添加新功能介绍
        self.add_new_features_info()
        
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = 600
        height = 500
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        """创建界面组件"""
        
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame = self.main_frame
        
        # 标题
        title_label = ttk.Label(main_frame, text="PDF拆分工具", 
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="选择PDF文件", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 文件路径显示
        self.file_path_var = tk.StringVar(value="请选择PDF文件...")
        file_path_label = ttk.Label(file_frame, textvariable=self.file_path_var,
                                   foreground="gray", font=("Arial", 10))
        file_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 选择文件按钮
        select_btn = ttk.Button(file_frame, text="浏览", command=self.select_file)
        select_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 拆分方式选择
        method_frame = ttk.LabelFrame(main_frame, text="拆分方式", padding="10")
        method_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.split_method = tk.StringVar(value="gui")
        
        # GUI模式
        gui_radio = ttk.Radiobutton(method_frame, text="可视化界面模式 (推荐)", 
                                   variable=self.split_method, value="gui")
        gui_radio.pack(anchor=tk.W, pady=(0, 5))
        
        gui_desc = ttk.Label(method_frame, text="• 提供PDF预览和可视化拆分点设置", 
                            font=("Arial", 9), foreground="gray")
        gui_desc.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))
        
        # 手动模式
        manual_radio = ttk.Radiobutton(method_frame, text="手动指定页码模式", 
                                      variable=self.split_method, value="manual")
        manual_radio.pack(anchor=tk.W, pady=(0, 5))
        
        manual_desc = ttk.Label(method_frame, text="• 直接输入拆分页码，用逗号分隔", 
                               font=("Arial", 9), foreground="gray")
        manual_desc.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))
        
        # 手动输入框
        manual_input_frame = ttk.Frame(method_frame)
        manual_input_frame.pack(fill=tk.X, padx=(20, 0))
        
        ttk.Label(manual_input_frame, text="拆分页码:").pack(side=tk.LEFT)
        self.manual_pages_var = tk.StringVar(value="3, 7, 10")
        manual_entry = ttk.Entry(manual_input_frame, textvariable=self.manual_pages_var, width=20)
        manual_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 智能模式
        smart_radio = ttk.Radiobutton(method_frame, text="智能拆分模式", 
                                     variable=self.split_method, value="smart")
        smart_radio.pack(anchor=tk.W, pady=(10, 5))
        
        smart_desc = ttk.Label(method_frame, text="• 根据PDF页数自动计算最佳拆分点", 
                              font=("Arial", 9), foreground="gray")
        smart_desc.pack(anchor=tk.W, padx=(20, 0))
        
        # 输出设置
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 输出文件夹
        folder_frame = ttk.Frame(output_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(folder_frame, text="输出文件夹:").pack(side=tk.LEFT)
        self.output_folder_var = tk.StringVar(value="与原文件相同位置")
        folder_label = ttk.Label(folder_frame, textvariable=self.output_folder_var,
                                foreground="gray", font=("Arial", 9))
        folder_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        folder_btn = ttk.Button(folder_frame, text="选择", command=self.select_output_folder)
        folder_btn.pack(side=tk.RIGHT)
        
        # 文件命名
        naming_frame = ttk.Frame(output_frame)
        naming_frame.pack(fill=tk.X)
        
        self.use_custom_names = tk.BooleanVar()
        custom_check = ttk.Checkbutton(naming_frame, text="使用自定义文件名", 
                                      variable=self.use_custom_names,
                                      command=self.toggle_custom_names)
        custom_check.pack(anchor=tk.W)
        
        self.custom_names_var = tk.StringVar(value="第一部分.pdf, 第二部分.pdf, 第三部分.pdf")
        self.custom_names_entry = ttk.Entry(naming_frame, textvariable=self.custom_names_var, 
                                           state="disabled", width=50)
        self.custom_names_entry.pack(fill=tk.X, pady=(5, 0))
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 开始拆分按钮
        split_btn = ttk.Button(button_frame, text="开始拆分", command=self.start_split,
                              style="Accent.TButton")
        split_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 测试按钮
        test_btn = ttk.Button(button_frame, text="使用测试文件", command=self.use_test_file)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 帮助按钮
        help_btn = ttk.Button(button_frame, text="使用帮助", command=self.show_help)
        help_btn.pack(side=tk.RIGHT)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                font=("Arial", 9), foreground="blue")
        status_label.pack(side=tk.BOTTOM, anchor=tk.W, pady=(10, 0))
        
    def select_file(self):
        """选择PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if file_path:
            self.selected_pdf = file_path
            self.file_path_var.set(os.path.basename(file_path))
            self.status_var.set(f"已选择: {os.path.basename(file_path)}")
            
    def select_output_folder(self):
        """选择输出文件夹"""
        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        
        if folder_path:
            self.output_folder_var.set(folder_path)
            
    def toggle_custom_names(self):
        """切换自定义文件名状态"""
        if self.use_custom_names.get():
            self.custom_names_entry.config(state="normal")
        else:
            self.custom_names_entry.config(state="disabled")
            
    def use_test_file(self):
        """使用测试文件"""
        test_files = [
            "测试材料/长图(编辑后).pdf",
            "测试材料/有字pdf.pdf", 
            "测试材料/无字pdf.pdf",
            "测试材料/asd.pdf"
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                self.selected_pdf = test_file
                self.file_path_var.set(os.path.basename(test_file))
                self.status_var.set(f"使用测试文件: {os.path.basename(test_file)}")
                messagebox.showinfo("测试文件", f"已选择测试文件:\n{os.path.basename(test_file)}")
                return
                
        messagebox.showwarning("测试文件", "未找到测试文件，请手动选择PDF文件")
        
    def start_split(self):
        """开始拆分"""
        if not self.selected_pdf:
            messagebox.showwarning("警告", "请先选择PDF文件")
            return
            
        if not os.path.exists(self.selected_pdf):
            messagebox.showerror("错误", "选择的文件不存在")
            return
            
        try:
            self.status_var.set("正在拆分...")
            self.root.update()
            
            # 准备参数
            split_points = None
            output_folder = None
            custom_names = None
            
            # 输出文件夹
            if self.output_folder_var.get() != "与原文件相同位置":
                output_folder = self.output_folder_var.get()
                
            # 自定义文件名
            if self.use_custom_names.get():
                names_text = self.custom_names_var.get().strip()
                if names_text:
                    custom_names = [name.strip() for name in names_text.split(",")]
            
            # 根据拆分方式处理
            method = self.split_method.get()
            
            if method == "manual":
                # 手动模式
                pages_text = self.manual_pages_var.get().strip()
                if pages_text:
                    try:
                        split_points = [int(p.strip()) for p in pages_text.split(",") if p.strip()]
                    except ValueError:
                        messagebox.showerror("错误", "页码格式不正确，请输入数字，用逗号分隔")
                        self.status_var.set("就绪")
                        return
                else:
                    messagebox.showwarning("警告", "请输入拆分页码")
                    self.status_var.set("就绪")
                    return
                    
            elif method == "smart":
                # 智能模式
                import fitz
                doc = fitz.open(self.selected_pdf)
                total_pages = len(doc)
                doc.close()
                
                if total_pages <= 5:
                    split_points = [total_pages // 2] if total_pages > 2 else []
                elif total_pages <= 20:
                    split_points = [total_pages // 3, 2 * total_pages // 3]
                else:
                    split_points = list(range(10, total_pages, 10))
                    
                split_points = [p for p in split_points if 1 <= p < total_pages]
                
                if not split_points:
                    messagebox.showinfo("提示", "文档页数较少，无需拆分")
                    self.status_var.set("就绪")
                    return
                    
                # 显示智能建议
                result = messagebox.askyesno("智能拆分建议", 
                                           f"PDF共{total_pages}页\n"
                                           f"建议拆分点: {split_points}\n"
                                           f"将生成{len(split_points)+1}个文件\n\n"
                                           f"是否使用此拆分方案?")
                if not result:
                    self.status_var.set("用户取消")
                    return
            
            # 执行拆分
            result = pdf_split(
                input_pdf_path=self.selected_pdf,
                split_points=split_points,
                output_folder=output_folder,
                custom_names=custom_names
            )
            
            if result:
                file_list = "\n".join([f"• {os.path.basename(f)}" for f in result])
                messagebox.showinfo("拆分完成", 
                                  f"成功生成 {len(result)} 个文件:\n\n{file_list}")
                self.status_var.set(f"拆分完成，生成{len(result)}个文件")
            else:
                messagebox.showerror("错误", "拆分失败或用户取消")
                self.status_var.set("拆分失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"拆分过程中出现错误:\n{str(e)}")
            self.status_var.set("拆分失败")
            
    def show_help(self):
        """显示帮助信息"""
        help_text = """PDF拆分工具使用帮助

📋 功能说明:
• 支持将PDF文件按页码拆分为多个独立文件
• 提供三种拆分模式：可视化界面、手动指定、智能拆分

🖥️ 可视化界面模式:
• 提供PDF预览功能
• 可视化设置拆分点
• 支持智能建议和批量设置
• 上下文预览：查看拆分点前后页面的文本内容
• 管理拆分点：列表显示所有拆分点，支持选择性删除
• 跳转到拆分点：快速跳转到指定的拆分点页面

✏️ 手动指定模式:
• 直接输入拆分页码
• 用逗号分隔多个页码
• 例如: 3, 7, 10

🧠 智能拆分模式:
• 根据PDF页数自动计算拆分点
• 小文档: 对半拆分
• 中等文档: 三等分
• 大文档: 每10页拆分

⚙️ 输出设置:
• 可选择输出文件夹
• 支持自定义文件名
• 默认使用原文件名+序号

🔧 高级操作:
• 双击拆分点列表项可直接删除
• 支持批量管理多个拆分点
• 实时预览拆分效果和文件数量

💡 使用技巧:
• 点击"使用测试文件"可快速选择测试PDF
• 建议先用可视化模式预览拆分效果
• 大文件建议使用智能拆分模式
• 使用"上下文预览"可以更好地确认拆分位置"""

        # 创建帮助窗口
        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("500x600")
        help_window.resizable(False, False)
        
        # 居中显示
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (250)
        y = (help_window.winfo_screenheight() // 2) - (300)
        help_window.geometry(f"500x600+{x}+{y}")
        
        # 创建文本框
        text_frame = ttk.Frame(help_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # 关闭按钮
        close_btn = ttk.Button(help_window, text="关闭", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def add_new_features_info(self):
        """添加新功能介绍"""
        # 在主界面底部添加新功能提示
        new_features_frame = ttk.LabelFrame(self.main_frame, text="🆕 最新功能", padding="10")
        new_features_frame.pack(fill="x", pady=(10, 0))
        
        features_text = """
✨ 新增强大的拆分点管理功能：
• 上下文预览：查看拆分点前后页面内容，确保拆分位置准确
• 智能管理：列表显示所有拆分点，支持选择性删除和跳转
• 快速操作：双击删除，一键跳转，提升操作效率
        """
        
        features_label = ttk.Label(new_features_frame, text=features_text, 
                                 font=("微软雅黑", 9), foreground="blue")
        features_label.pack(anchor="w")
        
        # 添加体验按钮
        experience_btn = ttk.Button(new_features_frame, text="🚀 立即体验新功能", 
                                  command=self.experience_new_features)
        experience_btn.pack(pady=(5, 0))
    
    def experience_new_features(self):
        """体验新功能"""
        messagebox.showinfo("新功能体验", 
                          "请选择一个PDF文件，然后选择'可视化界面模式'来体验新功能：\n\n"
                          "1. 设置几个拆分点\n"
                          "2. 点击'上下文预览'查看拆分点周围内容\n"
                          "3. 点击'管理拆分点'进行精确管理\n"
                          "4. 使用'跳转到拆分点'快速导航\n\n"
                          "这些功能让PDF拆分更加精确和高效！")


def main():
    """主函数"""
    # 检查依赖
    try:
        import fitz
        from pdf_fc import pdf_split
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所需依赖:")
        print("  pip install PyMuPDF")
        return
    
    # 创建主窗口
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    elif "clam" in style.theme_names():
        style.theme_use("clam")
    
    # 创建应用
    app = PDFSplitGUIDemo(root)
    
    # 运行应用
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行错误: {e}")


if __name__ == "__main__":
    main()