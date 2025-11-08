#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF拆分功能 - 简单GUI演示

这是一个最简单的GUI演示，展示如何调用pdf_split函数的GUI模式。
"""

def demo_gui_split():
    """演示GUI拆分功能"""
    print("🖥️  PDF拆分GUI演示")
    print("=" * 40)
    
    # 导入函数
    try:
        from pdf_fc import pdf_split
        print("✅ 成功导入pdf_split函数")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保pdf_fc.py文件在当前目录")
        return
    
    # 检查测试文件
    import os
    test_files = [
        "测试材料/长图(编辑后).pdf",
        "测试材料/有字pdf.pdf", 
        "测试材料/无字pdf.pdf",
        "测试材料/asd.pdf"
    ]
    
    available_files = [f for f in test_files if os.path.exists(f)]
    
    if not available_files:
        print("❌ 未找到测试PDF文件")
        print("请在以下位置放置测试PDF文件:")
        for f in test_files:
            print(f"  - {f}")
        print("\n或者修改代码中的文件路径")
        return
    
    # 使用第一个可用的测试文件
    test_file = available_files[0]
    print(f"📄 使用测试文件: {test_file}")
    
    print("\n🚀 启动GUI界面...")
    print("请在弹出的窗口中进行以下操作:")
    print("1. 浏览PDF页面 (上一页/下一页)")
    print("2. 设置拆分点 (点击'设为拆分点')")
    print("3. 或使用智能建议 (点击'智能建议')")
    print("4. 开始拆分 (点击'开始拆分')")
    print("\n注意: 如果没有弹出窗口，可能是Python环境问题")
    
    try:
        # 调用GUI模式 (不指定split_points参数)
        result = pdf_split(test_file)
        
        if result:
            print(f"\n✅ 拆分成功! 生成了 {len(result)} 个文件:")
            for i, file_path in enumerate(result, 1):
                print(f"  {i}. {os.path.basename(file_path)}")
        else:
            print("\n❌ 拆分失败或用户取消")
            
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        print("可能的原因:")
        print("  - Python环境配置问题")
        print("  - 缺少必要的依赖包")
        print("  - 图形界面不可用")


def demo_manual_split():
    """演示手动拆分功能"""
    print("\n📝 手动拆分演示")
    print("=" * 30)
    
    try:
        from pdf_fc import pdf_split
        import os
        
        # 查找测试文件
        test_files = [
            "测试材料/长图(编辑后).pdf",
            "测试材料/有字pdf.pdf", 
            "测试材料/无字pdf.pdf"
        ]
        
        test_file = None
        for f in test_files:
            if os.path.exists(f):
                test_file = f
                break
        
        if not test_file:
            print("❌ 未找到测试文件")
            return
        
        print(f"📄 使用文件: {test_file}")
        
        # 手动指定拆分点
        split_points = [2, 4]  # 在第2页和第4页后拆分
        print(f"📍 拆分点: {split_points}")
        
        # 执行拆分
        result = pdf_split(test_file, split_points=split_points)
        
        if result:
            print(f"✅ 手动拆分成功! 生成了 {len(result)} 个文件:")
            for i, file_path in enumerate(result, 1):
                print(f"  {i}. {os.path.basename(file_path)}")
        else:
            print("❌ 手动拆分失败")
            
    except Exception as e:
        print(f"❌ 手动拆分出错: {e}")


def main():
    """主函数"""
    print("🔧 PDF拆分功能演示程序")
    print("📅 演示时间:", end=" ")
    
    import datetime
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # 演示1: GUI模式
    demo_gui_split()
    
    # 演示2: 手动模式
    demo_manual_split()
    
    print("\n" + "=" * 50)
    print("🎉 演示完成!")
    print("\n💡 更多使用方法:")
    print("  - 运行 pdf_split_gui_demo.py 获得完整GUI界面")
    print("  - 运行 pdf_split_example.py 查看更多示例")
    print("  - 查看 PDF拆分功能使用说明.md 获得详细文档")


if __name__ == "__main__":
    main()