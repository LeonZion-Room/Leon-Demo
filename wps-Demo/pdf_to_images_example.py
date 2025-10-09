#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转图片功能使用示例

这个示例展示了如何使用 pdf_fc.py 中的 pdf_to_img 函数
将PDF文件转换为多张图片文件。

作者: AI Assistant
"""

import os
import sys
from pdf_fc import pdf_to_img
from file_path_fc import fc_path_get


def main():
    """主函数：演示PDF转图片的完整流程"""
    
    print("=== PDF转图片工具 ===")
    print("这个工具可以将PDF文件的每一页转换为单独的图片文件")
    print()
    
    # 方式1：使用文件选择器获取PDF路径
    print("请选择要转换的PDF文件...")
    try:
        pdf_path = fc_path_get()
        if not pdf_path:
            print("❌ 未选择文件，程序退出")
            return
        
        print(f"✅ 选择的文件: {pdf_path}")
        
    except Exception as e:
        print(f"❌ 文件选择失败: {e}")
        return
    
    # 询问用户选择输出格式
    print("\n请选择输出图片格式:")
    print("1. PNG (推荐，质量最好)")
    print("2. JPEG (文件较小)")
    
    while True:
        choice = input("请输入选择 (1 或 2): ").strip()
        if choice == '1':
            image_format = 'PNG'
            break
        elif choice == '2':
            image_format = 'JPEG'
            break
        else:
            print("❌ 无效选择，请输入 1 或 2")
    
    # 询问用户选择图片质量
    print(f"\n选择图片质量 (缩放因子):")
    print("1. 标准质量 (1.0x)")
    print("2. 高质量 (2.0x，推荐)")
    print("3. 超高质量 (3.0x)")
    
    zoom_factors = {'1': 1.0, '2': 2.0, '3': 3.0}
    while True:
        choice = input("请输入选择 (1, 2 或 3): ").strip()
        if choice in zoom_factors:
            zoom_factor = zoom_factors[choice]
            break
        else:
            print("❌ 无效选择，请输入 1, 2 或 3")
    
    print(f"\n开始转换...")
    print(f"📄 输入文件: {pdf_path}")
    print(f"🖼️  输出格式: {image_format}")
    print(f"🔍 缩放因子: {zoom_factor}x")
    print("-" * 50)
    
    # 执行转换
    try:
        output_folder = pdf_to_img(
            input_pdf_path=pdf_path,
            image_format=image_format,
            zoom_factor=zoom_factor
        )
        
        if output_folder:
            print("-" * 50)
            print("🎉 转换完成！")
            print(f"📁 输出文件夹: {output_folder}")
            
            # 显示生成的文件列表
            if os.path.exists(output_folder):
                files = sorted([f for f in os.listdir(output_folder) 
                              if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
                print(f"📄 生成的图片文件 ({len(files)} 个):")
                for i, filename in enumerate(files[:5], 1):  # 只显示前5个
                    print(f"  {i}. {filename}")
                if len(files) > 5:
                    print(f"  ... 还有 {len(files) - 5} 个文件")
            
            # 询问是否打开输出文件夹
            open_folder = input("\n是否打开输出文件夹? (y/n): ").strip().lower()
            if open_folder in ['y', 'yes', '是']:
                try:
                    os.startfile(output_folder)  # Windows
                except:
                    print(f"请手动打开文件夹: {output_folder}")
        else:
            print("❌ 转换失败！")
            
    except Exception as e:
        print(f"❌ 转换过程中出现错误: {e}")


def batch_convert_example():
    """批量转换示例"""
    
    print("=== 批量PDF转图片示例 ===")
    
    # 示例PDF文件列表（实际使用时需要替换为真实路径）
    pdf_files = [
        "document1.pdf",
        "document2.pdf", 
        "document3.pdf"
    ]
    
    # 转换设置
    image_format = 'PNG'
    zoom_factor = 2.0
    
    success_count = 0
    total_count = len(pdf_files)
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n处理文件 {i}/{total_count}: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            print(f"❌ 文件不存在，跳过: {pdf_path}")
            continue
        
        try:
            output_folder = pdf_to_img(
                input_pdf_path=pdf_path,
                image_format=image_format,
                zoom_factor=zoom_factor
            )
            
            if output_folder:
                print(f"✅ 转换成功: {output_folder}")
                success_count += 1
            else:
                print(f"❌ 转换失败: {pdf_path}")
                
        except Exception as e:
            print(f"❌ 转换错误: {e}")
    
    print(f"\n批量转换完成！成功: {success_count}/{total_count}")


def direct_call_example():
    """直接调用函数的示例"""
    
    print("=== 直接调用函数示例 ===")
    
    # 示例：直接指定PDF文件路径
    pdf_path = "example.pdf"  # 替换为实际的PDF文件路径
    
    if not os.path.exists(pdf_path):
        print(f"❌ 示例文件不存在: {pdf_path}")
        print("请将此路径替换为实际的PDF文件路径")
        return
    
    try:
        # 基本调用（使用默认参数）
        print("1. 基本调用（PNG格式，2.0x缩放）:")
        output_folder = pdf_to_img(pdf_path)
        print(f"输出文件夹: {output_folder}")
        
        # 自定义参数调用
        print("\n2. 自定义参数调用（JPEG格式，1.5x缩放）:")
        output_folder = pdf_to_img(
            input_pdf_path=pdf_path,
            image_format='JPEG',
            zoom_factor=1.5
        )
        print(f"输出文件夹: {output_folder}")
        
    except Exception as e:
        print(f"❌ 调用失败: {e}")


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'batch':
            batch_convert_example()
        elif mode == 'direct':
            direct_call_example()
        else:
            print("使用方法:")
            print("python pdf_to_images_example.py          # 交互式转换")
            print("python pdf_to_images_example.py batch    # 批量转换示例")
            print("python pdf_to_images_example.py direct   # 直接调用示例")
    else:
        # 默认运行交互式主程序
        main()