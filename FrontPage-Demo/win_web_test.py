#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows Web Test Tool
基于Dash实现的简单网站测试工具
支持通过命令行参数设置端口和标题
"""

import argparse
import sys
import webbrowser
from threading import Timer
import dash
from dash import html, dcc, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime


def create_app(title="Windows Web Test Tool"):
    """创建Dash应用"""
    app = dash.Dash(__name__)
    app.title = title
    
    # 示例数据
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, 11, 12, 13, 14],
        'category': ['A', 'B', 'A', 'B', 'A']
    })
    
    # 应用布局
    app.layout = html.Div([
        html.Div([
            html.H1(title, style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
            html.Hr(),
        ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),
        
        html.Div([
            html.Div([
                html.H3("系统信息", style={'color': '#34495e'}),
                html.P(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", id='start-time'),
                html.P("状态: 运行中", style={'color': 'green', 'fontWeight': 'bold'}),
                html.Button('刷新页面', id='refresh-btn', n_clicks=0, 
                           style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 
                                  'padding': '10px 20px', 'borderRadius': '5px', 'cursor': 'pointer'}),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 
                     'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),
            
            html.Div([
                html.H3("数据可视化", style={'color': '#34495e'}),
                dcc.Graph(
                    id='example-graph',
                    figure=px.line(df, x='x', y='y', color='category', 
                                  title='示例数据图表',
                                  template='plotly_white')
                ),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 
                     'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}),
            
            html.Div([
                html.H3("交互控件", style={'color': '#34495e'}),
                html.Label("选择图表类型:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='chart-type',
                    options=[
                        {'label': '折线图', 'value': 'line'},
                        {'label': '柱状图', 'value': 'bar'},
                        {'label': '散点图', 'value': 'scatter'}
                    ],
                    value='line',
                    style={'marginBottom': '20px'}
                ),
                html.Label("数值范围:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.RangeSlider(
                    id='range-slider',
                    min=1,
                    max=5,
                    step=1,
                    marks={i: str(i) for i in range(1, 6)},
                    value=[1, 5]
                ),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 
                     'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'}),
        
        html.Footer([
            html.P(f"© 2024 {title} - Python Dash Application", 
                  style={'textAlign': 'center', 'color': '#7f8c8d', 'marginTop': '40px'})
        ])
    ])
    
    # 回调函数：更新图表
    @app.callback(
        Output('example-graph', 'figure'),
        [Input('chart-type', 'value'),
         Input('range-slider', 'value')]
    )
    def update_graph(chart_type, range_values):
        filtered_df = df[(df['x'] >= range_values[0]) & (df['x'] <= range_values[1])]
        
        if chart_type == 'line':
            fig = px.line(filtered_df, x='x', y='y', color='category', 
                         title='动态折线图', template='plotly_white')
        elif chart_type == 'bar':
            fig = px.bar(filtered_df, x='x', y='y', color='category', 
                        title='动态柱状图', template='plotly_white')
        else:  # scatter
            fig = px.scatter(filtered_df, x='x', y='y', color='category', 
                           title='动态散点图', template='plotly_white')
        
        return fig
    
    # 回调函数：刷新时间
    @app.callback(
        Output('start-time', 'children'),
        [Input('refresh-btn', 'n_clicks')]
    )
    def update_time(n_clicks):
        return f"最后刷新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return app


def open_browser(url):
    """延迟打开浏览器"""
    webbrowser.open(url)


def get_user_input():
    """交互式获取用户输入参数"""
    print("=" * 60)
    print("🚀 Windows Web Test Tool - 配置向导")
    print("=" * 60)
    print("请按照提示输入配置参数（直接回车使用默认值）\n")
    
    # 获取端口
    while True:
        port_input = input("📡 请输入服务器端口 [默认: 8050]: ").strip()
        if not port_input:
            port = 8050
            break
        try:
            port = int(port_input)
            if 1 <= port <= 65535:
                break
            else:
                print("❌ 端口号必须在 1-65535 之间，请重新输入")
        except ValueError:
            print("❌ 请输入有效的数字")
    
    # 获取标题
    title_input = input("📝 请输入网站标题 [默认: Windows Web Test Tool]: ").strip()
    title = title_input if title_input else "Windows Web Test Tool"
    
    # 获取是否自动打开浏览器
    while True:
        browser_input = input("🌐 是否自动打开浏览器？(y/n) [默认: y]: ").strip().lower()
        if not browser_input or browser_input in ['y', 'yes', '是']:
            no_browser = False
            break
        elif browser_input in ['n', 'no', '否']:
            no_browser = True
            break
        else:
            print("❌ 请输入 y/n 或 是/否")
    
    # 获取是否启用调试模式
    while True:
        debug_input = input("🔧 是否启用调试模式？(y/n) [默认: n]: ").strip().lower()
        if not debug_input or debug_input in ['n', 'no', '否']:
            debug = False
            break
        elif debug_input in ['y', 'yes', '是']:
            debug = True
            break
        else:
            print("❌ 请输入 y/n 或 是/否")
    
    print("\n" + "=" * 60)
    print("✅ 配置完成！")
    print(f"📡 端口: {port}")
    print(f"📝 标题: {title}")
    print(f"🌐 自动打开浏览器: {'是' if not no_browser else '否'}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print("=" * 60)
    
    # 确认启动
    while True:
        confirm = input("\n🚀 确认启动服务器？(y/n) [默认: y]: ").strip().lower()
        if not confirm or confirm in ['y', 'yes', '是']:
            break
        elif confirm in ['n', 'no', '否']:
            print("👋 已取消启动")
            sys.exit(0)
        else:
            print("❌ 请输入 y/n 或 是/否")
    
    return port, title, no_browser, debug


def main():
    """主函数"""
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 有命令行参数，使用原来的方式
        parser = argparse.ArgumentParser(description='Windows Web Test Tool - 基于Dash的网站测试工具')
        parser.add_argument('-p', '--port', type=int, default=8050, 
                           help='设置服务器端口 (默认: 8050)')
        parser.add_argument('-t', '--title', type=str, default='Windows Web Test Tool', 
                           help='设置网站标题 (默认: Windows Web Test Tool)')
        parser.add_argument('--no-browser', action='store_true', 
                           help='不自动打开浏览器')
        parser.add_argument('--debug', action='store_true', 
                           help='启用调试模式')
        
        args = parser.parse_args()
        port = args.port
        title = args.title
        no_browser = args.no_browser
        debug = args.debug
    else:
        # 没有命令行参数，使用交互式输入
        port, title, no_browser, debug = get_user_input()
    
    # 创建应用
    app = create_app(title)
    
    # 服务器URL
    url = f"http://0.0.0.0:{port}"
    local_url = f"http://localhost:{port}"
    
    print("=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)
    print(f"📡 服务器地址: {url}")
    print(f"🌐 本地访问: {local_url}")
    print(f"⚙️  调试模式: {'开启' if debug else '关闭'}")
    print("=" * 60)
    print("💡 提示:")
    print("   - 按 Ctrl+C 停止服务器")
    print("   - 服务器允许所有IP访问")
    print("   - 可以通过局域网其他设备访问")
    print("=" * 60)
    
    # 自动打开浏览器
    if not no_browser:
        Timer(1.5, open_browser, args=[local_url]).start()
        print("🌐 正在打开浏览器...")
    
    try:
        # 启动服务器
        app.run(
            host='0.0.0.0',  # 允许所有IP访问
            port=port,
            debug=debug,
            use_reloader=False  # 避免在打包后出现问题
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()