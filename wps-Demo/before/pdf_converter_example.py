#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转纯图PDF完整示例
结合文件拖拽选择器和PDF转换功能
"""

import os
import sys
from file_path_fc import fc_path_get
from pdf_fc import pdf_to_imgpdf, pdf_to_imgpdf_with_options


def main():
    """主函数：完整的PDF转换流程"""
    print("=== PDF转纯图PDF工具 ===")
    print("这个工具可以将PDF文件转换为纯图PDF文件")
    print("转换后的文件将保存在原文件相同目录下，文件名后缀为'(纯图).pdf'")
    print()
    
    # 方式1：使用GUI文件选择器
    print("📁 请选择要转换的PDF文件...")
    print("即将打开文件选择器窗口...")
    
    try:
        # 调用文件选择器
        selected_file = fc_path_get()
        
        if not selected_file:
            print("❌ 未选择文件，程序退出")
            return
        
        print(f"✅ 已选择文件: {selected_file}")
        
        # 检查文件是否为PDF
        if not selected_file.lower().endswith('.pdf'):
            print("❌ 选择的文件不是PDF格式，请选择PDF文件")
            return
        
        # 显示文件信息
        file_size = os.path.getsize(selected_file)
        print(f"📊 文件大小: {file_size / 1024 / 1024:.2f} MB")
        
        # 询问用户是否要使用高级选项
        print("\n🔧 转换选项:")
        print("1. 标准转换 (推荐)")
        print("2. 高质量转换 (文件较大)")
        print("3. 压缩转换 (文件较小)")
        
        choice = input("请选择转换模式 (1-3，默认为1): ").strip()
        
        if choice == "2":
            # 高质量转换
            print("🚀 开始高质量转换...")
            result = pdf_to_imgpdf_with_options(
                selected_file, 
                zoom_factor=3.0,  # 更高的缩放因子
                image_format='PNG',
                optimize=False
            )
        elif choice == "3":
            # 压缩转换
            print("🚀 开始压缩转换...")
            result = pdf_to_imgpdf_with_options(
                selected_file,
                zoom_factor=1.5,  # 较低的缩放因子
                image_format='JPEG',
                optimize=True
            )
        else:
            # 标准转换
            print("🚀 开始标准转换...")
            result = pdf_to_imgpdf(selected_file)
        
        if result:
            print(f"\n🎉 转换成功！")
            print(f"📄 原文件: {selected_file}")
            print(f"📄 输出文件: {result}")
            
            # 显示输出文件信息
            if os.path.exists(result):
                output_size = os.path.getsize(result)
                print(f"📊 输出文件大小: {output_size / 1024 / 1024:.2f} MB")
                
                # 计算压缩比
                compression_ratio = (file_size - output_size) / file_size * 100
                if compression_ratio > 0:
                    print(f"📉 文件压缩了 {compression_ratio:.1f}%")
                else:
                    print(f"📈 文件增大了 {abs(compression_ratio):.1f}%")
            
            print("\n✨ 转换完成！你可以在原文件目录中找到转换后的PDF文件。")
        else:
            print("❌ 转换失败！")
            
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
    except ValueError as e:
        print(f"❌ 参数错误: {e}")
    except Exception as e:
        print(f"❌ 转换过程中发生错误: {e}")
        print("请检查文件是否损坏或者是否有足够的磁盘空间")


def batch_convert():
    """批量转换功能"""
    print("=== 批量PDF转换模式 ===")
    print("请将要转换的PDF文件放在一个文件夹中")
    
    # 选择文件夹
    print("📁 请选择包含PDF文件的文件夹...")
    folder_path = fc_path_get()  # 这里可以修改为选择文件夹的功能
    
    if not folder_path or not os.path.isdir(folder_path):
        print("❌ 未选择有效的文件夹")
        return
    
    # 查找PDF文件
    pdf_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith('.pdf'):
            pdf_files.append(os.path.join(folder_path, file))
    
    if not pdf_files:
        print("❌ 文件夹中没有找到PDF文件")
        return
    
    print(f"📋 找到 {len(pdf_files)} 个PDF文件")
    
    # 批量转换
    success_count = 0
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n🔄 正在转换第 {i}/{len(pdf_files)} 个文件: {os.path.basename(pdf_file)}")
        try:
            result = pdf_to_imgpdf(pdf_file)
            if result:
                success_count += 1
                print(f"✅ 转换成功")
            else:
                print(f"❌ 转换失败")
        except Exception as e:
            print(f"❌ 转换失败: {e}")
    
    print(f"\n🎉 批量转换完成！成功转换 {success_count}/{len(pdf_files)} 个文件")


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--batch":
            batch_convert()
        else:
            # 直接转换指定的PDF文件
            pdf_path = sys.argv[1]
            try:
                print(f"🚀 开始转换: {pdf_path}")
                result = pdf_to_imgpdf(pdf_path)
                if result:
                    print(f"✅ 转换成功: {result}")
                else:
                    print("❌ 转换失败")
            except Exception as e:
                print(f"❌ 错误: {e}")
    else:
        # 交互式模式
        main()