#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试img_fc.py中的图片分割和PDF生成功能
"""

import os
import sys
from img_fc import split_image_to_pdf

def test_split_image_to_pdf():
    """测试图片分割和PDF生成功能"""
    
    # 测试图片路径
    test_image_path = os.path.join("测试材料", "长图.png")
    
    # 检查测试图片是否存在
    if not os.path.exists(test_image_path):
        print(f"❌ 测试图片不存在: {test_image_path}")
        return False
    
    print(f"📸 找到测试图片: {test_image_path}")
    
    # 测试不同的分割份数
    test_cases = [2, 3, 4]
    
    for split_count in test_cases:
        print(f"\n🔄 测试分割份数: {split_count}")
        
        try:
            result_path = split_image_to_pdf(test_image_path, split_count)
            
            if result_path and os.path.exists(result_path):
                file_size = os.path.getsize(result_path)
                print(f"✅ 成功生成PDF: {os.path.basename(result_path)}")
                print(f"   文件大小: {file_size / 1024:.1f} KB")
                print(f"   完整路径: {result_path}")
            else:
                print(f"❌ PDF生成失败")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            return False
    
    print(f"\n🎉 所有测试通过！")
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("长图编辑功能测试")
    print("=" * 50)
    
    # 检查当前工作目录
    current_dir = os.getcwd()
    print(f"📁 当前目录: {current_dir}")
    
    # 列出测试材料文件夹中的文件
    test_materials_dir = "测试材料"
    if os.path.exists(test_materials_dir):
        print(f"📂 测试材料文件夹内容:")
        for file in os.listdir(test_materials_dir):
            file_path = os.path.join(test_materials_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"   - {file} ({size / 1024:.1f} KB)")
    else:
        print(f"❌ 测试材料文件夹不存在: {test_materials_dir}")
        return
    
    print("\n" + "=" * 50)
    
    # 运行测试
    success = test_split_image_to_pdf()
    
    if success:
        print("\n✅ 所有功能测试通过！")
        print("💡 你可以运行 'python img_fc.py' 来启动GUI界面进行交互式测试")
    else:
        print("\n❌ 测试失败，请检查代码")

if __name__ == "__main__":
    main()