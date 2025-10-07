#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template
import argparse
import sys

app = Flask(__name__)

# 全局变量存储配置
config = {
    'name': '个人介绍页面',
    'port': 5000
}

@app.route('/')
def index():
    """主页路由"""
    return render_template('index.html', name=config['name'])

@app.route('/api/info')
def api_info():
    """API接口，返回基本信息"""
    return {
        'name': config['name'],
        'port': config['port'],
        'status': 'running'
    }

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='简单的个人介绍页面')
    parser.add_argument('-p', '--port', type=int, default=5000, 
                       help='指定服务器端口 (默认: 5000)')
    parser.add_argument('-n', '--name', type=str, default='个人介绍页面',
                       help='指定页面名称 (默认: 个人介绍页面)')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    
    return parser.parse_args()

if __name__ == '__main__':
    # 解析命令行参数
    args = parse_arguments()
    
    # 更新配置
    config['name'] = args.name
    config['port'] = args.port
    
    print(f"启动服务器...")
    print(f"页面名称: {config['name']}")
    print(f"访问地址: http://localhost:{config['port']}")
    print(f"调试模式: {'开启' if args.debug else '关闭'}")
    print("-" * 50)
    
    try:
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=config['port'],
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)