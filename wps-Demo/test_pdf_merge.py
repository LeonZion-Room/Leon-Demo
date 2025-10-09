#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF合并工具测试脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入PDF合并功能
from pdf_fc import pdf_merge

def main():
    """
    主函数 - 启动PDF合并工具
    """
    print("=== PDF合并工具 ===")
    print("功能说明:")
    print("1. 可以选择多个PDF文件")
    print("2. 可以调整合并顺序（上移/下移）")
    print("3. 可以移除不需要的文件")
    print("4. 合并后输出为一个新的PDF文件")
    print("\n正在启动GUI界面...")
    
    try:
        # 启动PDF合并工具
        pdf_merge()
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()