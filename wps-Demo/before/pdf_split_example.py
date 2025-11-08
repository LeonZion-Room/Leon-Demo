#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF拆分功能示例代码

本文件演示了如何使用pdf_fc.py中的pdf_split函数进行PDF拆分操作。
包含了多种使用场景和示例。

作者: AI Assistant
日期: 2024
"""

import os
import sys
from pdf_fc import pdf_split


def example_basic_split():
    """示例1: 基本的PDF拆分功能"""
    print("=" * 50)
    print("示例1: 基本PDF拆分")
    print("=" * 50)
    
    # 假设有一个测试PDF文件
    pdf_file = "test_document.pdf"
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file):
        print(f"❌ 测试文件 {pdf_file} 不存在")
        print("请准备一个PDF文件并重命名为 test_document.pdf")
        return
    
    try:
        # 在第3页和第7页后拆分
        split_points = [3, 7]
        result = pdf_split(pdf_file, split_points=split_points)
        
        if result:
            print(f"✅ 拆分成功! 生成了 {len(result)} 个文件:")
            for i, file_path in enumerate(result, 1):
                print(f"  {i}. {os.path.basename(file_path)}")
        else:
            print("❌ 拆分失败")
            
    except Exception as e:
        print(f"❌ 拆分过程中出现错误: {e}")


def example_custom_output():
    """示例2: 自定义输出文件夹和文件名"""
    print("\n" + "=" * 50)
    print("示例2: 自定义输出设置")
    print("=" * 50)
    
    pdf_file = "test_document.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ 测试文件 {pdf_file} 不存在")
        return
    
    try:
        # 创建输出文件夹
        output_folder = "./pdf_split_output"
        os.makedirs(output_folder, exist_ok=True)
        
        # 自定义文件名
        custom_names = ["第一部分.pdf", "第二部分.pdf", "第三部分.pdf"]
        
        # 在第5页和第10页后拆分
        split_points = [5, 10]
        
        result = pdf_split(
            input_pdf_path=pdf_file,
            split_points=split_points,
            output_folder=output_folder,
            custom_names=custom_names
        )
        
        if result:
            print(f"✅ 拆分成功! 文件保存在 {output_folder} 文件夹:")
            for i, file_path in enumerate(result, 1):
                print(f"  {i}. {os.path.basename(file_path)}")
        else:
            print("❌ 拆分失败")
            
    except Exception as e:
        print(f"❌ 拆分过程中出现错误: {e}")


def example_gui_mode():
    """示例3: 使用GUI界面进行拆分"""
    print("\n" + "=" * 50)
    print("示例3: GUI界面拆分")
    print("=" * 50)
    
    pdf_file = "test_document.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ 测试文件 {pdf_file} 不存在")
        return
    
    try:
        print("正在启动GUI界面...")
        print("请在弹出的窗口中:")
        print("1. 使用上一页/下一页按钮浏览PDF")
        print("2. 在需要拆分的页面点击'设为拆分点'")
        print("3. 或者点击'智能建议'获取自动建议")
        print("4. 点击'开始拆分'完成操作")
        
        # 不指定split_points参数，将启动GUI界面
        result = pdf_split(pdf_file)
        
        if result:
            print(f"\n✅ GUI拆分完成! 生成了 {len(result)} 个文件:")
            for i, file_path in enumerate(result, 1):
                print(f"  {i}. {os.path.basename(file_path)}")
        else:
            print("\n❌ 用户取消了拆分操作或拆分失败")
            
    except Exception as e:
        print(f"❌ GUI拆分过程中出现错误: {e}")


def example_batch_split():
    """示例4: 批量拆分多个PDF文件"""
    print("\n" + "=" * 50)
    print("示例4: 批量PDF拆分")
    print("=" * 50)
    
    # 假设有多个PDF文件需要拆分
    pdf_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
    
    # 统一的拆分策略：每5页拆分一次
    split_interval = 5
    
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            print(f"⚠️  跳过不存在的文件: {pdf_file}")
            continue
        
        try:
            # 先获取PDF页数来计算拆分点
            import fitz
            doc = fitz.open(pdf_file)
            total_pages = len(doc)
            doc.close()
            
            # 计算拆分点
            split_points = list(range(split_interval, total_pages, split_interval))
            
            if not split_points:
                print(f"📄 {pdf_file} 页数较少，无需拆分")
                continue
            
            print(f"📄 正在拆分 {pdf_file} (总页数: {total_pages}, 拆分点: {split_points})")
            
            result = pdf_split(pdf_file, split_points=split_points)
            
            if result:
                print(f"  ✅ 成功生成 {len(result)} 个文件")
            else:
                print(f"  ❌ 拆分失败")
                
        except Exception as e:
            print(f"  ❌ 拆分 {pdf_file} 时出现错误: {e}")


def example_smart_split():
    """示例5: 智能拆分策略"""
    print("\n" + "=" * 50)
    print("示例5: 智能拆分策略")
    print("=" * 50)
    
    pdf_file = "test_document.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ 测试文件 {pdf_file} 不存在")
        return
    
    try:
        # 获取PDF信息
        import fitz
        doc = fitz.open(pdf_file)
        total_pages = len(doc)
        doc.close()
        
        print(f"📄 PDF文件: {pdf_file}")
        print(f"📊 总页数: {total_pages}")
        
        # 智能拆分策略
        if total_pages <= 5:
            split_points = [total_pages // 2] if total_pages > 2 else []
            strategy = "小文档策略: 对半拆分"
        elif total_pages <= 20:
            split_points = [total_pages // 3, 2 * total_pages // 3]
            strategy = "中等文档策略: 三等分"
        else:
            # 大文档：每10页拆分
            split_points = list(range(10, total_pages, 10))
            strategy = "大文档策略: 每10页拆分"
        
        # 过滤有效拆分点
        split_points = [p for p in split_points if 1 <= p < total_pages]
        
        print(f"🧠 {strategy}")
        print(f"📍 拆分点: {split_points}")
        
        if not split_points:
            print("💡 文档太小，无需拆分")
            return
        
        result = pdf_split(pdf_file, split_points=split_points)
        
        if result:
            print(f"✅ 智能拆分完成! 生成了 {len(result)} 个文件:")
            for i, file_path in enumerate(result, 1):
                file_size = os.path.getsize(file_path) / 1024  # KB
                print(f"  {i}. {os.path.basename(file_path)} ({file_size:.1f} KB)")
        else:
            print("❌ 智能拆分失败")
            
    except Exception as e:
        print(f"❌ 智能拆分过程中出现错误: {e}")


def main():
    """主函数：运行所有示例"""
    print("🔧 PDF拆分功能示例程序")
    print("📚 本程序演示了pdf_split函数的各种用法")
    print()
    
    # 检查是否有测试文件
    test_files = ["test_document.pdf", "doc1.pdf", "doc2.pdf", "doc3.pdf"]
    available_files = [f for f in test_files if os.path.exists(f)]
    
    if not available_files:
        print("⚠️  注意: 当前目录下没有找到测试PDF文件")
        print("请准备以下任一文件来运行示例:")
        for file in test_files:
            print(f"  - {file}")
        print()
        print("或者修改示例代码中的文件路径")
        print()
    
    # 运行示例
    try:
        # 示例1: 基本拆分
        example_basic_split()
        
        # 示例2: 自定义输出
        example_custom_output()
        
        # 示例3: GUI模式 (注释掉，避免在自动化测试中弹窗)
        # example_gui_mode()
        
        # 示例4: 批量拆分
        example_batch_split()
        
        # 示例5: 智能拆分
        example_smart_split()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断了程序")
    except Exception as e:
        print(f"\n\n❌ 程序运行出现错误: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 示例程序运行完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()