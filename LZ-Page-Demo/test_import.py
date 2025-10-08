"""
测试脚本：验证lz_fc模块的导入和使用
"""

# 导入lz_fc模块
from lz_fc import show_lz_window

def test_import():
    """测试导入功能"""
    print("成功导入lz_fc模块!")
    print("可以使用 show_lz_window() 函数来显示窗口")
    
    # 询问用户是否要显示窗口
    user_input = input("是否要显示LZ-Studio窗口? (y/n): ")
    if user_input.lower() in ['y', 'yes', '是']:
        print("正在显示窗口...")
        show_lz_window()
    else:
        print("测试完成，未显示窗口")

if __name__ == "__main__":
    test_import()