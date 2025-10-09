#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化测试原有文本编辑功能
"""

import os
import sys
from pdf_fc import PDFEditor

def test_text_extraction():
    """测试文本提取功能"""
    print("🔍 测试文本提取功能...")
    
    # 使用之前成功加载的PDF文件
    test_pdf = "C:/Users/leonz/Downloads/有字pdf.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ 文件不存在: {test_pdf}")
        return False
    
    try:
        # 创建编辑器实例
        editor = PDFEditor(test_pdf)
        
        # 提取所有文本
        editor.extract_all_text()
        
        print(f"✅ 成功提取 {len(editor.existing_texts)} 个文本元素")
        
        # 显示前5个文本元素的信息
        for i, text_info in enumerate(editor.existing_texts[:5]):
            text_preview = text_info['text'][:30].replace('\n', ' ')
            print(f"文本 {i+1}: '{text_preview}...' 在页面 {text_info['page']}")
        
        # 测试获取特定页面的文本
        if editor.existing_texts:
            page_0_texts = editor.get_page_existing_texts(0)
            print(f"✅ 第1页有 {len(page_0_texts)} 个文本元素")
            
            # 显示第一页的前3个文本
            for i, text_info in enumerate(page_0_texts[:3]):
                text_preview = text_info['text'][:20].replace('\n', ' ')
                rect = text_info['rect']
                print(f"  - 文本: '{text_preview}' 位置: ({rect[0]:.1f}, {rect[1]:.1f})")
        
        editor.close()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_text_position_detection():
    """测试文本位置检测功能"""
    print("\n🎯 测试文本位置检测功能...")
    
    test_pdf = "C:/Users/leonz/Downloads/有字pdf.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ 文件不存在: {test_pdf}")
        return False
    
    try:
        editor = PDFEditor(test_pdf)
        editor.extract_all_text()
        
        if not editor.existing_texts:
            print("❌ 没有找到文本元素")
            return False
        
        # 测试第一个文本元素的位置检测
        first_text = editor.existing_texts[0]
        rect = first_text['rect']
        
        # 测试点击文本中心位置
        center_x = (rect[0] + rect[2]) / 2
        center_y = (rect[1] + rect[3]) / 2
        
        print(f"测试文本: '{first_text['text'][:30]}...'")
        print(f"文本位置: ({rect[0]:.1f}, {rect[1]:.1f}, {rect[2]:.1f}, {rect[3]:.1f})")
        print(f"测试点击位置: ({center_x:.1f}, {center_y:.1f})")
        
        found_text = editor.find_text_at_position(center_x, center_y, first_text['page'])
        
        if found_text:
            print(f"✅ 成功检测到文本: '{found_text['text'][:30]}...'")
            editor.close()
            return True
        else:
            print("❌ 未能检测到文本")
            editor.close()
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_text_editing_methods():
    """测试文本编辑方法"""
    print("\n✏️ 测试文本编辑方法...")
    
    test_pdf = "C:/Users/leonz/Downloads/有字pdf.pdf"
    
    if not os.path.exists(test_pdf):
        print(f"❌ 文件不存在: {test_pdf}")
        return False
    
    try:
        editor = PDFEditor(test_pdf)
        editor.extract_all_text()
        
        if not editor.existing_texts:
            print("❌ 没有找到文本元素")
            return False
        
        # 测试删除文本方法
        first_text = editor.existing_texts[0]
        print(f"测试删除文本: '{first_text['text'][:30]}...'")
        
        # 这里只是测试方法调用，不实际保存
        try:
            editor.delete_existing_text(first_text)
            print("✅ 删除文本方法调用成功")
        except Exception as e:
            print(f"❌ 删除文本方法失败: {str(e)}")
            return False
        
        # 测试替换文本方法
        print("测试替换文本方法...")
        try:
            editor.replace_existing_text(first_text, "测试替换文本", 12, "black", "Arial")
            print("✅ 替换文本方法调用成功")
        except Exception as e:
            print(f"❌ 替换文本方法失败: {str(e)}")
            return False
        
        editor.close()
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 原有文本编辑功能自动化测试")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # 测试文本提取
    if test_text_extraction():
        tests_passed += 1
    
    # 测试文本位置检测
    if test_text_position_detection():
        tests_passed += 1
    
    # 测试文本编辑方法
    if test_text_editing_methods():
        tests_passed += 1
    
    print(f"\n📊 测试结果: {tests_passed}/{total_tests} 通过")
    
    if tests_passed == total_tests:
        print("✅ 所有测试通过！")
        print("💡 提示: 现在可以在GUI中测试以下功能:")
        print("   1. 选择'编辑原有文本'模式")
        print("   2. 点击PDF中的文本进行选择")
        print("   3. 在文本框中修改内容")
        print("   4. 点击'替换文本'或'删除文本'按钮")
    else:
        print("❌ 部分测试失败，请检查实现")

if __name__ == "__main__":
    main()