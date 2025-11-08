import fitz  # PyMuPDF
import os
from PIL import Image
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
from matplotlib.figure import Figure
import numpy as np


def pdf_to_imgpdf(input_pdf_path):
    """
    将PDF转换为纯图PDF
    
    Args:
        input_pdf_path (str): 输入PDF文件的路径
        
    Returns:
        str: 输出PDF文件的路径，如果转换失败则返回None
        
    Raises:
        FileNotFoundError: 当输入文件不存在时
        Exception: 当转换过程中出现错误时
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {input_pdf_path}")
    
    # 检查文件是否为PDF
    if not input_pdf_path.lower().endswith('.pdf'):
        raise ValueError("输入文件必须是PDF格式")
    
    try:
        # 生成输出文件路径
        input_dir = os.path.dirname(input_pdf_path)
        input_filename = os.path.basename(input_pdf_path)
        name_without_ext = os.path.splitext(input_filename)[0]
        output_pdf_path = os.path.join(input_dir, f"{name_without_ext}(纯图).pdf")
        
        print(f"开始转换PDF: {input_pdf_path}")
        print(f"输出文件: {output_pdf_path}")
        
        # 打开输入PDF
        input_doc = fitz.open(input_pdf_path)
        
        # 创建新的PDF文档
        output_doc = fitz.open()
        
        # 设置渲染参数
        zoom = 2.0  # 缩放因子，提高图像质量
        mat = fitz.Matrix(zoom, zoom)
        
        total_pages = len(input_doc)
        print(f"总页数: {total_pages}")
        
        # 逐页处理
        for page_num in range(total_pages):
            print(f"正在处理第 {page_num + 1}/{total_pages} 页...")
            
            # 获取页面
            page = input_doc[page_num]
            
            # 将页面渲染为图像
            pix = page.get_pixmap(matrix=mat)
            
            # 将pixmap转换为PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # 优化图像质量（可选）
            # 如果需要压缩，可以调整质量参数
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG', optimize=True)
            img_buffer.seek(0)
            
            # 创建新页面
            img_rect = fitz.Rect(0, 0, pix.width, pix.height)
            new_page = output_doc.new_page(width=pix.width, height=pix.height)
            
            # 将图像插入到新页面
            new_page.insert_image(img_rect, stream=img_buffer.getvalue())
            
            # 清理资源
            img_buffer.close()
            pix = None
        
        # 保存输出PDF
        output_doc.save(output_pdf_path)
        
        # 关闭文档
        input_doc.close()
        output_doc.close()
        
        print(f"✅ PDF转换完成: {output_pdf_path}")
        return output_pdf_path
        
    except Exception as e:
        print(f"❌ PDF转换失败: {str(e)}")
        # 确保文档被正确关闭
        try:
            if 'input_doc' in locals():
                input_doc.close()
            if 'output_doc' in locals():
                output_doc.close()
        except:
            pass
        raise e


def pdf_to_imgpdf_with_options(input_pdf_path, zoom_factor=2.0, image_format='PNG', optimize=True):
    """
    将PDF转换为纯图PDF（带更多选项）
    
    Args:
        input_pdf_path (str): 输入PDF文件的路径
        zoom_factor (float): 缩放因子，默认2.0（影响图像质量）
        image_format (str): 图像格式，默认'PNG'
        optimize (bool): 是否优化图像，默认True
        
    Returns:
        str: 输出PDF文件的路径，如果转换失败则返回None
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {input_pdf_path}")
    
    # 检查文件是否为PDF
    if not input_pdf_path.lower().endswith('.pdf'):
        raise ValueError("输入文件必须是PDF格式")
    
    try:
        # 生成输出文件路径
        input_dir = os.path.dirname(input_pdf_path)
        input_filename = os.path.basename(input_pdf_path)
        name_without_ext = os.path.splitext(input_filename)[0]
        output_pdf_path = os.path.join(input_dir, f"{name_without_ext}(纯图).pdf")
        
        print(f"开始转换PDF: {input_pdf_path}")
        print(f"输出文件: {output_pdf_path}")
        print(f"缩放因子: {zoom_factor}")
        print(f"图像格式: {image_format}")
        
        # 打开输入PDF
        input_doc = fitz.open(input_pdf_path)
        
        # 创建新的PDF文档
        output_doc = fitz.open()
        
        # 设置渲染参数
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        
        total_pages = len(input_doc)
        print(f"总页数: {total_pages}")
        
        # 逐页处理
        for page_num in range(total_pages):
            print(f"正在处理第 {page_num + 1}/{total_pages} 页...")
            
            # 获取页面
            page = input_doc[page_num]
            
            # 将页面渲染为图像
            pix = page.get_pixmap(matrix=mat)
            
            # 将pixmap转换为PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # 处理图像
            img_buffer = io.BytesIO()
            if image_format.upper() == 'JPEG':
                # JPEG格式，可以设置质量
                img = img.convert('RGB')  # JPEG不支持透明度
                img.save(img_buffer, format='JPEG', quality=95, optimize=optimize)
            else:
                # PNG格式
                img.save(img_buffer, format='PNG', optimize=optimize)
            
            img_buffer.seek(0)
            
            # 创建新页面
            img_rect = fitz.Rect(0, 0, pix.width, pix.height)
            new_page = output_doc.new_page(width=pix.width, height=pix.height)
            
            # 将图像插入到新页面
            new_page.insert_image(img_rect, stream=img_buffer.getvalue())
            
            # 清理资源
            img_buffer.close()
            pix = None
        
        # 保存输出PDF
        output_doc.save(output_pdf_path)
        
        # 关闭文档
        input_doc.close()
        output_doc.close()
        
        print(f"✅ PDF转换完成: {output_pdf_path}")
        return output_pdf_path
        
    except Exception as e:
        print(f"❌ PDF转换失败: {str(e)}")
        # 确保文档被正确关闭
        try:
            if 'input_doc' in locals():
                input_doc.close()
            if 'output_doc' in locals():
                output_doc.close()
        except:
            pass
        raise e


# 测试函数（可选）
def pdf_to_img(input_pdf_path, image_format='PNG', zoom_factor=2.0):
    """
    将PDF转换为多张图片，每页一张图片
    
    Args:
        input_pdf_path (str): 输入PDF文件的路径
        image_format (str): 输出图片格式，支持 'PNG', 'JPEG', 'JPG'
        zoom_factor (float): 缩放因子，影响图片质量和大小
        
    Returns:
        str: 输出文件夹路径，如果转换失败则返回None
        
    Raises:
        FileNotFoundError: 当输入文件不存在时
        Exception: 当转换过程中出现错误时
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {input_pdf_path}")
    
    # 检查文件是否为PDF
    if not input_pdf_path.lower().endswith('.pdf'):
        raise ValueError("输入文件必须是PDF格式")
    
    # 验证图片格式
    supported_formats = ['PNG', 'JPEG', 'JPG']
    image_format = image_format.upper()
    if image_format not in supported_formats:
        raise ValueError(f"不支持的图片格式: {image_format}，支持的格式: {supported_formats}")
    
    try:
        # 生成输出文件夹路径
        input_dir = os.path.dirname(input_pdf_path)
        input_filename = os.path.basename(input_pdf_path)
        name_without_ext = os.path.splitext(input_filename)[0]
        output_folder = os.path.join(input_dir, name_without_ext)
        
        # 创建输出文件夹
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"创建输出文件夹: {output_folder}")
        else:
            print(f"使用现有文件夹: {output_folder}")
        
        print(f"开始转换PDF: {input_pdf_path}")
        print(f"输出格式: {image_format}")
        print(f"缩放因子: {zoom_factor}")
        
        # 打开PDF文档
        doc = fitz.open(input_pdf_path)
        
        # 设置渲染参数
        mat = fitz.Matrix(zoom_factor, zoom_factor)
        
        total_pages = len(doc)
        print(f"总页数: {total_pages}")
        
        # 逐页处理
        for page_num in range(total_pages):
            print(f"正在处理第 {page_num + 1}/{total_pages} 页...")
            
            # 获取页面
            page = doc[page_num]
            
            # 将页面渲染为图像
            pix = page.get_pixmap(matrix=mat)
            
            # 生成输出文件名（页码从1开始，补零对齐）
            page_number = str(page_num + 1).zfill(len(str(total_pages)))
            if image_format == 'JPEG' or image_format == 'JPG':
                output_filename = f"page_{page_number}.jpg"
                pil_format = 'JPEG'
            else:
                output_filename = f"page_{page_number}.png"
                pil_format = 'PNG'
            
            output_path = os.path.join(output_folder, output_filename)
            
            # 将pixmap转换为PIL Image并保存
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # 如果是JPEG格式，需要转换为RGB模式（去除透明通道）
            if pil_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # 保存图片
            if pil_format == 'JPEG':
                img.save(output_path, format=pil_format, quality=95, optimize=True)
            else:
                img.save(output_path, format=pil_format, optimize=True)
            
            print(f"  ✅ 保存: {output_filename}")
            
            # 清理资源
            pix = None
        
        # 关闭文档
        doc.close()
        
        print(f"🎉 PDF转图片完成！")
        print(f"📁 输出文件夹: {output_folder}")
        print(f"📄 共生成 {total_pages} 张图片")
        
        return output_folder
        
    except Exception as e:
        print(f"❌ PDF转图片失败: {str(e)}")
        # 确保文档被正确关闭
        try:
            if 'doc' in locals():
                doc.close()
        except:
            pass
        return None


def pdf2docx(pdf_path, docx_path=None, progress_cb=None):
    """
    将PDF文件转换为DOCX文件
    
    使用Microsoft Word COM接口进行转换，需要系统安装Microsoft Word
    
    Args:
        pdf_path (str): 输入PDF文件的路径
        docx_path (str, optional): 输出DOCX文件的路径，如果不指定则自动生成
        
    Returns:
        str: 输出DOCX文件的路径，如果转换失败则返回None
        
    Raises:
        FileNotFoundError: 当输入文件不存在时
        ImportError: 当comtypes库未安装时
        Exception: 当转换过程中出现错误时
        
    Requirements:
        - 需要安装Microsoft Word
        - 需要安装comtypes库: pip install comtypes
        
    Example:
        >>> # 基本用法
        >>> result = pdf2docx("test.pdf")
        >>> print(f"转换完成: {result}")
        
        >>> # 指定输出路径
        >>> result = pdf2docx("input.pdf", "output.docx")
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {pdf_path}")
    
    # 检查文件是否为PDF
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError("输入文件必须是PDF格式")
    
    # 如果没有指定输出路径，自动生成
    if docx_path is None:
        input_dir = os.path.dirname(pdf_path)
        input_filename = os.path.basename(pdf_path)
        name_without_ext = os.path.splitext(input_filename)[0]
        docx_path = os.path.join(input_dir, f"{name_without_ext}.docx")
    
    # 确保输出路径以.docx结尾
    if not docx_path.lower().endswith('.docx'):
        docx_path += '.docx'
    
    try:
        # 导入comtypes库
        try:
            import comtypes.client
        except ImportError:
            raise ImportError("需要安装comtypes库: pip install comtypes")
        
        def report(pct, msg):
            try:
                if progress_cb:
                    progress_cb(int(pct), str(msg))
                else:
                    print(f"[{int(pct):3d}%] {msg}")
            except Exception:
                # 回调异常不影响主流程
                print(f"[{int(pct):3d}%] {msg}")

        report(0, f"开始转换PDF到DOCX: {pdf_path}")
        print(f"输出文件: {docx_path}")
        
        # 创建Word应用程序对象
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False  # 后台运行，不显示窗口
        report(10, "已启动Word应用")
        
        try:
            # 将路径转换为绝对路径
            pdf_path_abs = os.path.abspath(pdf_path)
            docx_path_abs = os.path.abspath(docx_path)
            
            report(20, "正在打开PDF文件...")
            # 打开PDF文件
            doc = word.Documents.Open(pdf_path_abs)
            report(40, "已打开PDF文件")
            
            report(50, "正在转换为DOCX格式...")
            # 保存为DOCX格式 (FileFormat=16 对应 docx 格式)
            doc.SaveAs2(docx_path_abs, FileFormat=16)
            report(95, "已保存DOCX文件")
            
            # 关闭文档
            doc.Close()
            
            report(100, f"✅ PDF转DOCX完成: {docx_path}")
            return docx_path
            
        except Exception as e:
            report(100, f"❌ 转换过程中出现错误: {str(e)}")
            # 尝试关闭可能打开的文档
            try:
                if 'doc' in locals():
                    doc.Close()
            except:
                pass
            raise e
            
        finally:
            # 确保Word应用程序被关闭
            try:
                word.Quit()
            except:
                pass
                
    except Exception as e:
        print(f"❌ PDF转DOCX失败: {str(e)}")
        return None


def pdf2docx_batch(pdf_folder, output_folder=None, progress_cb=None):
    """
    批量将文件夹中的PDF文件转换为DOCX文件
    
    Args:
        pdf_folder (str): 包含PDF文件的文件夹路径
        output_folder (str, optional): 输出文件夹路径，如果不指定则使用输入文件夹
        
    Returns:
        list: 成功转换的文件路径列表
        
    Example:
        >>> # 批量转换当前文件夹的所有PDF
        >>> results = pdf2docx_batch("./pdfs")
        >>> print(f"成功转换 {len(results)} 个文件")
    """
    
    if not os.path.exists(pdf_folder):
        raise FileNotFoundError(f"文件夹不存在: {pdf_folder}")
    
    if not os.path.isdir(pdf_folder):
        raise ValueError("输入路径必须是文件夹")
    
    # 如果没有指定输出文件夹，使用输入文件夹
    if output_folder is None:
        output_folder = pdf_folder
    else:
        # 创建输出文件夹（如果不存在）
        os.makedirs(output_folder, exist_ok=True)
    
    # 查找所有PDF文件
    pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ 文件夹中没有找到PDF文件")
        return []
    
    total = len(pdf_files)
    print(f"找到 {total} 个PDF文件，开始批量转换...")
    
    successful_conversions = []
    failed_conversions = []
    
    def report(pct, msg):
        try:
            if progress_cb:
                progress_cb(int(pct), str(msg))
            else:
                print(f"[{int(pct):3d}%] {msg}")
        except Exception:
            print(f"[{int(pct):3d}%] {msg}")

    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        name_without_ext = os.path.splitext(pdf_file)[0]
        docx_path = os.path.join(output_folder, f"{name_without_ext}.docx")
        
        print(f"\n[{i}/{len(pdf_files)}] 转换: {pdf_file}")
        report(((i-1) * 100) / total, f"开始转换 {pdf_file}")
        
        try:
            result = pdf2docx(pdf_path, docx_path, progress_cb=progress_cb)
            if result:
                successful_conversions.append(result)
                print(f"  ✅ 成功")
            else:
                failed_conversions.append(pdf_file)
                print(f"  ❌ 失败")
        except Exception as e:
            failed_conversions.append(pdf_file)
            print(f"  ❌ 失败: {str(e)}")
        finally:
            report((i * 100) / total, f"完成转换 {pdf_file}")
    
    print(f"\n🎉 批量转换完成!")
    print(f"✅ 成功: {len(successful_conversions)} 个文件")
    print(f"❌ 失败: {len(failed_conversions)} 个文件")
    report(100, "批量转换完成")
    
    if failed_conversions:
        print("失败的文件:")
        for failed_file in failed_conversions:
            print(f"  - {failed_file}")
    
    return successful_conversions


def pdf_split(input_pdf_path, split_points=None, output_folder=None, custom_names=None):
    """
    PDF拆分功能：将PDF文件按指定页码拆分为多个文件
    
    Args:
        input_pdf_path (str): 输入PDF文件的路径
        split_points (list): 拆分点页码列表，例如 [3, 7, 10] 表示在第3、7、10页后拆分
                           如果为None，则弹出GUI界面让用户选择拆分点
        output_folder (str): 输出文件夹路径，如果为None则使用输入文件所在目录
        custom_names (list): 自定义输出文件名列表，如果为None则使用默认命名
        
    Returns:
        list: 输出文件路径列表，如果拆分失败则返回None
        
    Example:
        >>> # 基本用法：在第3页和第7页后拆分
        >>> result = pdf_split("document.pdf", split_points=[3, 7])
        >>> print(f"生成了 {len(result)} 个文件")
        
        >>> # 自定义输出文件夹和文件名
        >>> result = pdf_split("document.pdf", 
        ...                    split_points=[5, 10], 
        ...                    output_folder="./output",
        ...                    custom_names=["part1.pdf", "part2.pdf", "part3.pdf"])
        
        >>> # 使用GUI界面选择拆分点
        >>> result = pdf_split("document.pdf")
    """
    
    # 检查输入文件是否存在
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"输入文件不存在: {input_pdf_path}")
    
    # 检查文件是否为PDF
    if not input_pdf_path.lower().endswith('.pdf'):
        raise ValueError("输入文件必须是PDF格式")
    
    try:
        # 打开PDF文档
        doc = fitz.open(input_pdf_path)
        total_pages = len(doc)
        
        print(f"开始拆分PDF: {input_pdf_path}")
        print(f"总页数: {total_pages}")
        
        # 如果没有指定拆分点，启动GUI界面
        if split_points is None:
            doc.close()  # 先关闭文档
            return pdf_split_gui(input_pdf_path)
        
        # 验证拆分点
        if not isinstance(split_points, list):
            raise ValueError("拆分点必须是列表格式")
        
        # 过滤和排序拆分点
        valid_split_points = []
        for point in split_points:
            if isinstance(point, int) and 1 <= point < total_pages:
                valid_split_points.append(point)
            else:
                print(f"警告: 忽略无效拆分点 {point} (必须在1到{total_pages-1}之间)")
        
        valid_split_points = sorted(list(set(valid_split_points)))  # 去重并排序
        
        if not valid_split_points:
            print("❌ 没有有效的拆分点")
            doc.close()
            return None
        
        print(f"有效拆分点: {valid_split_points}")
        
        # 设置输出文件夹
        if output_folder is None:
            output_folder = os.path.dirname(input_pdf_path)
        else:
            os.makedirs(output_folder, exist_ok=True)
        
        # 生成输出文件路径
        input_filename = os.path.basename(input_pdf_path)
        name_without_ext = os.path.splitext(input_filename)[0]
        
        output_files = []
        
        # 计算每个部分的页面范围
        ranges = []
        start_page = 0
        
        for split_point in valid_split_points:
            ranges.append((start_page, split_point - 1))  # 转换为0索引
            start_page = split_point
        
        # 添加最后一个范围
        ranges.append((start_page, total_pages - 1))
        
        print(f"拆分范围: {ranges}")
        
        # 拆分PDF
        for i, (start, end) in enumerate(ranges):
            print(f"正在生成第 {i + 1}/{len(ranges)} 个文件 (第{start+1}-{end+1}页)...")
            
            # 生成输出文件名
            if custom_names and i < len(custom_names):
                output_filename = custom_names[i]
                if not output_filename.lower().endswith('.pdf'):
                    output_filename += '.pdf'
            else:
                output_filename = f"{name_without_ext}_part{i+1}.pdf"
            
            output_path = os.path.join(output_folder, output_filename)
            
            # 创建新的PDF文档
            new_doc = fitz.open()
            
            # 复制指定范围的页面
            for page_num in range(start, end + 1):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            
            # 保存文件
            new_doc.save(output_path)
            new_doc.close()
            
            output_files.append(output_path)
            print(f"  ✅ 生成: {output_filename}")
        
        # 关闭原文档
        doc.close()
        
        print(f"🎉 PDF拆分完成! 生成了 {len(output_files)} 个文件")
        return output_files
        
    except Exception as e:
        print(f"❌ PDF拆分失败: {str(e)}")
        # 确保文档被正确关闭
        try:
            if 'doc' in locals():
                doc.close()
            if 'new_doc' in locals():
                new_doc.close()
        except:
            pass
        raise e


def pdf_split_gui(input_pdf_path):
    """
    PDF拆分GUI界面：提供可视化的PDF拆分功能
    
    Args:
        input_pdf_path (str): 输入PDF文件的路径
        
    Returns:
        list: 输出文件路径列表，如果用户取消则返回None
    """
    
    # 检查输入文件
    if not os.path.exists(input_pdf_path):
        messagebox.showerror("错误", f"文件不存在: {input_pdf_path}")
        return None
    
    try:
        # 打开PDF文档获取页数
        doc = fitz.open(input_pdf_path)
        total_pages = len(doc)
        doc.close()
        
        if total_pages <= 1:
            messagebox.showwarning("警告", "PDF文件只有1页，无法拆分")
            return None
        
    except Exception as e:
        messagebox.showerror("错误", f"无法读取PDF文件: {str(e)}")
        return None
    
    # 用于存储结果
    result_files = None
    split_markers = []
    current_page = 0
    
    # 创建主窗口
    root = tk.Tk()
    root.title("PDF拆分工具")
    root.geometry("800x600")
    root.resizable(True, True)
    
    # 设置窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (400)
    y = (root.winfo_screenheight() // 2) - (300)
    root.geometry(f"800x600+{x}+{y}")
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题区域
    title_frame = ttk.Frame(main_frame)
    title_frame.pack(fill=tk.X, pady=(0, 10))
    
    title_label = ttk.Label(title_frame, text="PDF拆分预览", font=("Arial", 16, "bold"))
    title_label.pack(side=tk.LEFT)
    
    file_label = ttk.Label(title_frame, text=f"文件: {os.path.basename(input_pdf_path)} | 总页数: {total_pages}", 
                          font=("Arial", 10), foreground="gray")
    file_label.pack(side=tk.RIGHT)
    
    # 创建PDF预览区域
    preview_frame = ttk.LabelFrame(main_frame, text="PDF预览", padding="5")
    preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # 创建matplotlib图形
    fig = Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, preview_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # 页面导航区域
    nav_frame = ttk.Frame(main_frame)
    nav_frame.pack(fill=tk.X, pady=(0, 10))
    
    ttk.Button(nav_frame, text="上一页", command=lambda: change_page(-1)).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(nav_frame, text="下一页", command=lambda: change_page(1)).pack(side=tk.LEFT, padx=(0, 5))
    
    page_label = ttk.Label(nav_frame, text="", font=("Arial", 11))
    page_label.pack(side=tk.LEFT, padx=(10, 0))
    
    # 拆分控制区域
    split_frame = ttk.LabelFrame(main_frame, text="拆分控制", padding="5")
    split_frame.pack(fill=tk.X, pady=(0, 10))
    
    # 第一行按钮
    split_row1 = ttk.Frame(split_frame)
    split_row1.pack(fill=tk.X, pady=(0, 5))
    
    ttk.Button(split_row1, text="设为拆分点", command=add_split_marker).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(split_row1, text="清除拆分点", command=clear_split_markers).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(split_row1, text="智能建议", command=smart_suggest).pack(side=tk.LEFT, padx=(0, 5))
    
    # 拆分信息显示
    info_label = ttk.Label(split_row1, text="", font=("Arial", 10), foreground="blue")
    info_label.pack(side=tk.RIGHT)
    
    # 第二行按钮 - 新增功能
    split_row2 = ttk.Frame(split_frame)
    split_row2.pack(fill=tk.X, pady=(0, 5))
    
    ttk.Button(split_row2, text="上下文预览", command=lambda: show_context_preview()).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(split_row2, text="管理拆分点", command=lambda: manage_split_points()).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(split_row2, text="跳转到拆分点", command=lambda: jump_to_split_point()).pack(side=tk.LEFT, padx=(0, 5))
    
    # 按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    ttk.Button(button_frame, text="开始拆分", command=start_split).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text="取消", command=root.quit).pack(side=tk.RIGHT)
    
    def show_current_page():
        """显示当前页面"""
        try:
            doc = fitz.open(input_pdf_path)
            page = doc[current_page]
            
            # 渲染页面为图像
            mat = fitz.Matrix(1.5, 1.5)  # 缩放因子
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # 转换为PIL图像
            img = Image.open(io.BytesIO(img_data))
            
            # 清除之前的内容
            ax.clear()
            
            # 显示图像
            ax.imshow(img)
            ax.set_title(f"第 {current_page + 1} 页", fontsize=14)
            ax.axis('off')
            
            # 如果当前页是拆分点，添加标记
            if (current_page + 1) in split_markers:
                ax.text(0.02, 0.98, "📍 拆分点", transform=ax.transAxes, 
                       fontsize=12, color='red', weight='bold',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.8),
                       verticalalignment='top')
            
            canvas.draw()
            doc.close()
            
        except Exception as e:
            ax.clear()
            ax.text(0.5, 0.5, f"无法显示页面: {str(e)}", 
                   ha='center', va='center', transform=ax.transAxes)
            canvas.draw()
    
    def change_page(direction):
        """切换页面"""
        nonlocal current_page
        new_page = current_page + direction
        if 0 <= new_page < total_pages:
            current_page = new_page
            show_current_page()
            update_page_label()
    
    def update_page_label():
        """更新页面标签"""
        page_label.config(text=f"第 {current_page + 1} / {total_pages} 页")
        update_split_info()
    
    def add_split_marker():
        """添加拆分点"""
        page_num = current_page + 1
        if page_num == total_pages:
            messagebox.showwarning("警告", "不能在最后一页设置拆分点")
            return
        
        if page_num not in split_markers:
            split_markers.append(page_num)
            split_markers.sort()
            show_current_page()  # 刷新显示
            update_split_info()
            messagebox.showinfo("成功", f"已在第 {page_num} 页设置拆分点")
        else:
            messagebox.showinfo("提示", f"第 {page_num} 页已经是拆分点")
    
    def clear_split_markers():
        """清除所有拆分点"""
        if split_markers:
            split_markers.clear()
            show_current_page()
            update_split_info()
            messagebox.showinfo("成功", "已清除所有拆分点")
        else:
            messagebox.showinfo("提示", "当前没有拆分点")
    
    def smart_suggest():
        """智能建议拆分点"""
        if total_pages <= 5:
            suggested = [total_pages // 2]
        elif total_pages <= 10:
            suggested = [total_pages // 3, 2 * total_pages // 3]
        else:
            # 每5-10页一个拆分点
            interval = max(5, total_pages // 5)
            suggested = list(range(interval, total_pages, interval))
        
        # 过滤有效的拆分点
        suggested = [p for p in suggested if 1 <= p < total_pages]
        
        if suggested:
            result = messagebox.askyesno("智能建议", 
                                       f"建议在以下页面设置拆分点:\n{suggested}\n\n是否应用这些建议?")
            if result:
                split_markers.clear()
                split_markers.extend(suggested)
                split_markers.sort()
                show_current_page()
                update_split_info()
        else:
            messagebox.showinfo("提示", "当前页数较少，无需拆分")
    
    def update_split_info():
        """更新拆分信息"""
        if not split_markers:
            info_label.config(text="未设置拆分点")
        else:
            file_count = len(split_markers) + 1
            info_label.config(text=f"拆分点: {split_markers} | 将生成 {file_count} 个文件")
    
    def show_context_preview():
        """显示上下文预览窗口"""
        if not split_markers:
            messagebox.showinfo("提示", "请先设置拆分点")
            return
        
        # 创建预览窗口
        preview_window = tk.Toplevel(root)
        preview_window.title("拆分点上下文预览")
        preview_window.geometry("900x700")
        preview_window.resizable(True, True)
        
        # 设置窗口居中
        preview_window.update_idletasks()
        x = (preview_window.winfo_screenwidth() // 2) - (450)
        y = (preview_window.winfo_screenheight() // 2) - (350)
        preview_window.geometry(f"900x700+{x}+{y}")
        
        # 创建主框架
        preview_main_frame = ttk.Frame(preview_window, padding="10")
        preview_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(preview_main_frame, text="拆分点上下文预览", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建滚动框架
        canvas_frame = ttk.Frame(preview_main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 显示每个拆分点的上下文
        try:
            doc = fitz.open(input_pdf_path)
            
            for i, split_point in enumerate(split_markers):
                # 创建拆分点框架
                split_frame = ttk.LabelFrame(scrollable_frame, 
                                           text=f"拆分点 {i+1}: 第 {split_point} 页", 
                                           padding="10")
                split_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
                
                # 显示前一页、当前页、后一页
                pages_to_show = []
                if split_point > 1:
                    pages_to_show.append((split_point - 1, "前一页"))
                pages_to_show.append((split_point, "拆分页"))
                if split_point < total_pages:
                    pages_to_show.append((split_point + 1, "后一页"))
                
                for page_num, page_desc in pages_to_show:
                    page_frame = ttk.Frame(split_frame)
                    page_frame.pack(fill=tk.X, pady=2)
                    
                    # 页面信息
                    page_info = ttk.Label(page_frame, text=f"{page_desc} (第 {page_num} 页)", 
                                         font=("Arial", 10, "bold"))
                    page_info.pack(anchor=tk.W)
                    
                    # 获取页面文本内容（前100个字符）
                    try:
                        page = doc[page_num - 1]
                        text_content = page.get_text()
                        if text_content.strip():
                            preview_text = text_content.strip()[:100] + "..." if len(text_content) > 100 else text_content.strip()
                        else:
                            preview_text = "[此页面无文本内容]"
                    except:
                        preview_text = "[无法获取页面内容]"
                    
                    text_label = ttk.Label(page_frame, text=preview_text, 
                                         font=("Arial", 9), foreground="gray",
                                         wraplength=800)
                    text_label.pack(anchor=tk.W, padx=(20, 0))
            
            doc.close()
            
        except Exception as e:
            error_label = ttk.Label(scrollable_frame, 
                                  text=f"无法加载预览: {str(e)}", 
                                  font=("Arial", 10), foreground="red")
            error_label.pack(pady=20)
        
        # 关闭按钮
        close_btn = ttk.Button(preview_main_frame, text="关闭", 
                              command=preview_window.destroy)
        close_btn.pack(pady=(10, 0))
    
    def manage_split_points():
        """管理拆分点窗口"""
        if not split_markers:
            messagebox.showinfo("提示", "当前没有拆分点")
            return
        
        # 创建管理窗口
        manage_window = tk.Toplevel(root)
        manage_window.title("管理拆分点")
        manage_window.geometry("500x400")
        manage_window.resizable(True, True)
        
        # 设置窗口居中
        manage_window.update_idletasks()
        x = (manage_window.winfo_screenwidth() // 2) - (250)
        y = (manage_window.winfo_screenheight() // 2) - (200)
        manage_window.geometry(f"500x400+{x}+{y}")
        
        # 创建主框架
        manage_main_frame = ttk.Frame(manage_window, padding="10")
        manage_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(manage_main_frame, text="拆分点管理", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建列表框架
        list_frame = ttk.LabelFrame(manage_main_frame, text="当前拆分点", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建Treeview
        columns = ("序号", "页码", "操作")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        tree.heading("序号", text="序号")
        tree.heading("页码", text="页码")
        tree.heading("操作", text="操作")
        
        # 设置列宽
        tree.column("序号", width=60, anchor=tk.CENTER)
        tree.column("页码", width=100, anchor=tk.CENTER)
        tree.column("操作", width=200, anchor=tk.CENTER)
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        def refresh_tree():
            """刷新树形列表"""
            for item in tree.get_children():
                tree.delete(item)
            
            for i, page_num in enumerate(split_markers, 1):
                tree.insert("", "end", values=(i, f"第 {page_num} 页", "双击删除"))
        
        def on_item_double_click(event):
            """双击删除拆分点"""
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                page_text = item['values'][1]
                page_num = int(page_text.replace("第 ", "").replace(" 页", ""))
                
                result = messagebox.askyesno("确认删除", 
                                           f"确定要删除第 {page_num} 页的拆分点吗？")
                if result:
                    split_markers.remove(page_num)
                    refresh_tree()
                    show_current_page()  # 刷新主界面
                    update_split_info()
                    messagebox.showinfo("成功", f"已删除第 {page_num} 页的拆分点")
        
        tree.bind("<Double-1>", on_item_double_click)
        
        # 按钮框架
        button_frame = ttk.Frame(manage_main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 0))
        
        def delete_selected():
            """删除选中的拆分点"""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请先选择要删除的拆分点")
                return
            
            item = tree.item(selection[0])
            page_text = item['values'][1]
            page_num = int(page_text.replace("第 ", "").replace(" 页", ""))
            
            result = messagebox.askyesno("确认删除", 
                                       f"确定要删除第 {page_num} 页的拆分点吗？")
            if result:
                split_markers.remove(page_num)
                refresh_tree()
                show_current_page()  # 刷新主界面
                update_split_info()
                messagebox.showinfo("成功", f"已删除第 {page_num} 页的拆分点")
        
        def jump_to_selected():
            """跳转到选中的拆分点"""
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请先选择要跳转的拆分点")
                return
            
            item = tree.item(selection[0])
            page_text = item['values'][1]
            page_num = int(page_text.replace("第 ", "").replace(" 页", ""))
            
            nonlocal current_page
            current_page = page_num - 1  # 转换为0基索引
            show_current_page()
            update_page_label()
            manage_window.destroy()
            messagebox.showinfo("跳转成功", f"已跳转到第 {page_num} 页")
        
        ttk.Button(button_frame, text="删除选中", command=delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="跳转到选中页", command=jump_to_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="关闭", command=manage_window.destroy).pack(side=tk.RIGHT)
        
        # 初始化列表
        refresh_tree()
    
    def jump_to_split_point():
        """跳转到拆分点"""
        if not split_markers:
            messagebox.showinfo("提示", "当前没有拆分点")
            return
        
        # 创建选择对话框
        jump_window = tk.Toplevel(root)
        jump_window.title("跳转到拆分点")
        jump_window.geometry("300x200")
        jump_window.resizable(False, False)
        
        # 设置窗口居中
        jump_window.update_idletasks()
        x = (jump_window.winfo_screenwidth() // 2) - (150)
        y = (jump_window.winfo_screenheight() // 2) - (100)
        jump_window.geometry(f"300x200+{x}+{y}")
        
        # 创建主框架
        jump_main_frame = ttk.Frame(jump_window, padding="20")
        jump_main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(jump_main_frame, text="选择要跳转的拆分点", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 15))
        
        # 拆分点选择
        selected_page = tk.StringVar()
        
        for page_num in split_markers:
            rb = ttk.Radiobutton(jump_main_frame, 
                               text=f"第 {page_num} 页", 
                               variable=selected_page, 
                               value=str(page_num))
            rb.pack(anchor=tk.W, pady=2)
        
        # 默认选择第一个
        if split_markers:
            selected_page.set(str(split_markers[0]))
        
        # 按钮框架
        button_frame = ttk.Frame(jump_main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        def do_jump():
            """执行跳转"""
            if selected_page.get():
                page_num = int(selected_page.get())
                nonlocal current_page
                current_page = page_num - 1  # 转换为0基索引
                show_current_page()
                update_page_label()
                jump_window.destroy()
                messagebox.showinfo("跳转成功", f"已跳转到第 {page_num} 页")
        
        ttk.Button(button_frame, text="跳转", command=do_jump).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="取消", command=jump_window.destroy).pack(side=tk.RIGHT)
    
    def start_split():
        """开始拆分"""
        nonlocal result_files
        
        if not split_markers:
            messagebox.showwarning("警告", "请先设置拆分点")
            return
        
        try:
            # 调用核心拆分函数
            result_files = pdf_split(input_pdf_path, split_points=split_markers)
            
            if result_files:
                file_list = "\n".join([os.path.basename(f) for f in result_files])
                messagebox.showinfo("拆分完成", f"成功生成 {len(result_files)} 个文件:\n\n{file_list}")
                root.quit()
            else:
                messagebox.showerror("错误", "拆分失败")
        
        except Exception as e:
            messagebox.showerror("错误", f"拆分过程中出现错误:\n{str(e)}")
    
    # 初始化显示
    show_current_page()
    update_page_label()
    
    # 运行GUI
    root.mainloop()
    root.destroy()
    
    return result_files


def pdf_merge():
    """
    PDF合并GUI界面：提供可视化的PDF合并功能
    
    Returns:
        str: 输出文件路径，如果用户取消则返回None
    """
    
    # 用于存储结果
    result_file = None
    pdf_files = []
    
    # 创建主窗口
    root = tk.Tk()
    root.title("PDF合并工具")
    root.geometry("700x500")
    root.resizable(True, True)
    
    # 设置窗口居中
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (350)
    y = (root.winfo_screenheight() // 2) - (250)
    root.geometry(f"700x500+{x}+{y}")
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题区域
    title_frame = ttk.Frame(main_frame)
    title_frame.pack(fill=tk.X, pady=(0, 15))
    
    title_label = ttk.Label(title_frame, text="PDF合并工具", font=("Arial", 16, "bold"))
    title_label.pack(side=tk.LEFT)
    
    # 文件列表区域
    list_frame = ttk.LabelFrame(main_frame, text="待合并的PDF文件", padding="5")
    list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
    
    # 创建Treeview来显示文件列表
    columns = ("序号", "文件名", "路径")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
    
    # 设置列标题
    tree.heading("序号", text="序号")
    tree.heading("文件名", text="文件名")
    tree.heading("路径", text="文件路径")
    
    # 设置列宽
    tree.column("序号", width=60, anchor=tk.CENTER)
    tree.column("文件名", width=200, anchor=tk.W)
    tree.column("路径", width=400, anchor=tk.W)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 文件操作按钮区域
    file_ops_frame = ttk.Frame(main_frame)
    file_ops_frame.pack(fill=tk.X, pady=(0, 15))
    
    def add_files():
        """添加PDF文件"""
        files = filedialog.askopenfilenames(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        for file_path in files:
            if file_path not in pdf_files:
                pdf_files.append(file_path)
                refresh_file_list()
    
    def remove_selected():
        """移除选中的文件"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移除的文件")
            return
        
        # 获取选中项的索引
        indices_to_remove = []
        for item in selection:
            index = tree.index(item)
            indices_to_remove.append(index)
        
        # 按倒序删除，避免索引变化
        for index in sorted(indices_to_remove, reverse=True):
            if 0 <= index < len(pdf_files):
                pdf_files.pop(index)
        
        refresh_file_list()
    
    def move_up():
        """上移选中的文件"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移动的文件")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("警告", "一次只能移动一个文件")
            return
        
        index = tree.index(selection[0])
        if index > 0:
            pdf_files[index], pdf_files[index-1] = pdf_files[index-1], pdf_files[index]
            refresh_file_list()
            # 重新选中移动后的项
            new_item = tree.get_children()[index-1]
            tree.selection_set(new_item)
    
    def move_down():
        """下移选中的文件"""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要移动的文件")
            return
        
        if len(selection) > 1:
            messagebox.showwarning("警告", "一次只能移动一个文件")
            return
        
        index = tree.index(selection[0])
        if index < len(pdf_files) - 1:
            pdf_files[index], pdf_files[index+1] = pdf_files[index+1], pdf_files[index]
            refresh_file_list()
            # 重新选中移动后的项
            new_item = tree.get_children()[index+1]
            tree.selection_set(new_item)
    
    def clear_all():
        """清空所有文件"""
        if pdf_files:
            if messagebox.askyesno("确认", "确定要清空所有文件吗？"):
                pdf_files.clear()
                refresh_file_list()
    
    def refresh_file_list():
        """刷新文件列表显示"""
        # 清空现有项
        for item in tree.get_children():
            tree.delete(item)
        
        # 添加文件项
        for i, file_path in enumerate(pdf_files):
            filename = os.path.basename(file_path)
            tree.insert("", tk.END, values=(i+1, filename, file_path))
    
    # 文件操作按钮
    ttk.Button(file_ops_frame, text="添加文件", command=add_files).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(file_ops_frame, text="移除选中", command=remove_selected).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(file_ops_frame, text="上移", command=move_up).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(file_ops_frame, text="下移", command=move_down).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(file_ops_frame, text="清空", command=clear_all).pack(side=tk.LEFT, padx=(0, 5))
    
    # 状态信息
    status_label = ttk.Label(file_ops_frame, text="", font=("Arial", 10), foreground="blue")
    status_label.pack(side=tk.RIGHT)
    
    def update_status():
        """更新状态信息"""
        if pdf_files:
            status_label.config(text=f"已选择 {len(pdf_files)} 个文件")
        else:
            status_label.config(text="请添加PDF文件")
    
    def start_merge():
        """开始合并PDF"""
        nonlocal result_file
        
        if len(pdf_files) < 2:
            messagebox.showwarning("警告", "至少需要选择2个PDF文件进行合并")
            return
        
        # 选择输出文件
        output_file = filedialog.asksaveasfilename(
            title="保存合并后的PDF文件",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf")]
        )
        
        if not output_file:
            return
        
        try:
            # 执行合并
            messagebox.showinfo("提示", "开始合并PDF文件，请稍候...")
            
            # 创建新的PDF文档
            merged_doc = fitz.open()
            
            for i, pdf_path in enumerate(pdf_files):
                try:
                    # 打开PDF文件
                    doc = fitz.open(pdf_path)
                    
                    # 将所有页面插入到合并文档中
                    merged_doc.insert_pdf(doc)
                    
                    # 关闭文档
                    doc.close()
                    
                    print(f"已合并: {os.path.basename(pdf_path)} ({i+1}/{len(pdf_files)})")
                    
                except Exception as e:
                    messagebox.showerror("错误", f"合并文件 {os.path.basename(pdf_path)} 时出错:\n{str(e)}")
                    merged_doc.close()
                    return
            
            # 保存合并后的文档
            merged_doc.save(output_file)
            merged_doc.close()
            
            result_file = output_file
            
            # 显示成功信息
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            messagebox.showinfo("合并完成", 
                              f"PDF合并成功！\n\n"
                              f"输出文件: {os.path.basename(output_file)}\n"
                              f"文件大小: {file_size:.2f} MB\n"
                              f"合并了 {len(pdf_files)} 个文件")
            
            root.quit()
            
        except Exception as e:
            messagebox.showerror("错误", f"合并过程中出现错误:\n{str(e)}")
    
    # 主操作按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    ttk.Button(button_frame, text="开始合并", command=start_merge).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(button_frame, text="取消", command=root.quit).pack(side=tk.RIGHT)
    
    # 绑定文件列表变化事件
    def on_file_list_change():
        update_status()
    
    # 初始化状态
    update_status()
    
    # 运行GUI
    root.mainloop()
    root.destroy()
    
    return result_file
