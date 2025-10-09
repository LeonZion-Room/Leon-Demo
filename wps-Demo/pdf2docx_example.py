#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转DOCX功能使用示例
"""

from pdf_fc import pdf2docx, pdf2docx_batch
from file_path_fc import fc_path_get
import os

def example_single_conversion():
    """示例：单个文件转换"""
    print("=" * 50)
    print("示例：单个PDF文件转换为DOCX")
    print("=" * 50)
    
    # 使用文件选择器选择PDF文件
    print("请选择要转换的PDF文件...")
    pdf_file = fc_path_get()
    
    if not pdf_file:
        print("❌ 未选择文件，退出")
        return
    
    if not pdf_file.lower().endswith('.pdf'):
        print("❌ 请选择PDF文件")
        return
    
    print(f"选择的文件: {pdf_file}")
    
    try:
        # 转换PDF到DOCX
        result = pdf2docx(pdf_file)
        
        if result:
            print(f"✅ 转换成功！")
            print(f"输出文件: {result}")
            print(f"文件大小: {os.path.getsize(result)} 字节")
        else:
            print("❌ 转换失败")
            
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")

def example_batch_conversion():
    """示例：批量转换"""
    print("\n" + "=" * 50)
    print("示例：批量转换文件夹中的PDF文件")
    print("=" * 50)
    
    # 使用文件选择器选择文件夹（这里简化为直接使用测试文件夹）
    folder_path = "测试材料"
    
    if not os.path.exists(folder_path):
        print(f"❌ 文件夹不存在: {folder_path}")
        return
    
    print(f"批量转换文件夹: {folder_path}")
    
    try:
        # 批量转换
        results = pdf2docx_batch(folder_path)
        
        if results:
            print(f"✅ 批量转换完成！")
            print(f"成功转换 {len(results)} 个文件:")
            for result in results:
                print(f"  - {os.path.basename(result)}")
        else:
            print("❌ 没有文件被转换")
            
    except Exception as e:
        print(f"❌ 批量转换失败: {str(e)}")

def example_custom_output():
    """示例：自定义输出路径"""
    print("\n" + "=" * 50)
    print("示例：自定义输出路径转换")
    print("=" * 50)
    
    # 使用测试文件
    pdf_file = "测试材料/有字pdf.pdf"
    custom_output = "测试材料/自定义输出文件名.docx"
    
    if not os.path.exists(pdf_file):
        print(f"❌ 测试文件不存在: {pdf_file}")
        return
    
    print(f"输入文件: {pdf_file}")
    print(f"自定义输出: {custom_output}")
    
    try:
        # 转换并指定输出路径
        result = pdf2docx(pdf_file, custom_output)
        
        if result:
            print(f"✅ 转换成功！")
            print(f"输出文件: {result}")
        else:
            print("❌ 转换失败")
            
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")

def main():
    """主函数"""
    print("PDF转DOCX功能使用示例")
    print("=" * 50)
    
    # 检查系统要求
    try:
        import comtypes.client
        print("✅ 系统要求满足")
    except ImportError:
        print("❌ 需要安装comtypes库: pip install comtypes")
        return
    
    # 运行示例
    try:
        # 示例1：单个文件转换
        example_single_conversion()
        
        # 示例2：批量转换
        example_batch_conversion()
        
        # 示例3：自定义输出路径
        example_custom_output()
        
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")

if __name__ == "__main__":
    main()