#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转DOCX功能测试脚本
"""

import os
import sys
from pdf_fc import pdf2docx, pdf2docx_batch

def test_pdf2docx():
    """测试pdf2docx函数"""
    print("=" * 50)
    print("测试 pdf2docx 函数")
    print("=" * 50)
    
    # 测试文件路径
    test_folder = "测试材料"
    
    if not os.path.exists(test_folder):
        print(f"❌ 测试文件夹不存在: {test_folder}")
        return False
    
    # 查找测试PDF文件
    pdf_files = [f for f in os.listdir(test_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ 测试文件夹中没有PDF文件: {test_folder}")
        return False
    
    print(f"找到 {len(pdf_files)} 个测试PDF文件:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    
    # 测试第一个PDF文件
    test_pdf = os.path.join(test_folder, pdf_files[0])
    print(f"\n开始测试转换: {test_pdf}")
    
    try:
        result = pdf2docx(test_pdf)
        if result and os.path.exists(result):
            print(f"✅ 转换成功: {result}")
            print(f"文件大小: {os.path.getsize(result)} 字节")
            return True
        else:
            print("❌ 转换失败: 未生成输出文件")
            return False
    except Exception as e:
        print(f"❌ 转换失败: {str(e)}")
        return False

def test_pdf2docx_batch():
    """测试批量转换功能"""
    print("\n" + "=" * 50)
    print("测试 pdf2docx_batch 函数")
    print("=" * 50)
    
    test_folder = "测试材料"
    
    if not os.path.exists(test_folder):
        print(f"❌ 测试文件夹不存在: {test_folder}")
        return False
    
    try:
        results = pdf2docx_batch(test_folder)
        if results:
            print(f"✅ 批量转换成功，共转换 {len(results)} 个文件")
            return True
        else:
            print("❌ 批量转换失败或没有文件被转换")
            return False
    except Exception as e:
        print(f"❌ 批量转换失败: {str(e)}")
        return False

def check_requirements():
    """检查系统要求"""
    print("检查系统要求...")
    
    # 检查comtypes库
    try:
        import comtypes.client
        print("✅ comtypes库已安装")
    except ImportError:
        print("❌ comtypes库未安装，请运行: pip install comtypes")
        return False
    
    # 检查是否为Windows系统
    if os.name != 'nt':
        print("❌ 此功能需要Windows系统和Microsoft Word")
        return False
    
    print("✅ 系统要求检查通过")
    return True

def main():
    """主测试函数"""
    print("PDF转DOCX功能测试")
    print("=" * 50)
    
    # 检查系统要求
    if not check_requirements():
        print("\n❌ 系统要求不满足，无法进行测试")
        return
    
    # 测试单个文件转换
    success1 = test_pdf2docx()
    
    # 测试批量转换
    success2 = test_pdf2docx_batch()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    if success1 and success2:
        print("🎉 所有测试通过！PDF转DOCX功能正常工作")
    else:
        print("❌ 部分测试失败，请检查错误信息")
        if not success1:
            print("  - 单个文件转换测试失败")
        if not success2:
            print("  - 批量转换测试失败")

if __name__ == "__main__":
    main()