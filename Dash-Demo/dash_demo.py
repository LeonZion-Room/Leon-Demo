import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime, timedelta
import queue

# 初始化Dash应用，使用Bootstrap主题
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 全局变量用于多线程通信
data_queue = queue.Queue()
background_running = False
background_thread = None

# 生成示例数据
def generate_sample_data():
    """生成示例数据用于图表展示"""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)
    sales = np.random.normal(1000, 200, len(dates))
    profit = sales * np.random.uniform(0.1, 0.3, len(dates))
    
    df = pd.DataFrame({
        'date': dates,
        'sales': sales,
        'profit': profit,
        'category': np.random.choice(['A', 'B', 'C'], len(dates))
    })
    return df

# 后台任务函数
def background_task():
    """后台线程任务，模拟实时数据更新"""
    global background_running
    while background_running:
        # 模拟数据处理
        current_time = datetime.now().strftime("%H:%M:%S")
        random_value = np.random.randint(1, 100)
        
        # 将数据放入队列
        data_queue.put({
            'time': current_time,
            'value': random_value,
            'status': '运行中'
        })
        
        time.sleep(2)  # 每2秒更新一次

# 获取示例数据
df = generate_sample_data()

# 应用布局
app.layout = dbc.Container([
    # 标题栏
    dbc.Row([
        dbc.Col([
            html.H1("🚀 Dash 多功能演示应用", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # 控制面板
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🎛️ 控制面板"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("选择图表类型:"),
                            dcc.Dropdown(
                                id='chart-type-dropdown',
                                options=[
                                    {'label': '📊 柱状图', 'value': 'bar'},
                                    {'label': '📈 折线图', 'value': 'line'},
                                    {'label': '🥧 饼图', 'value': 'pie'},
                                    {'label': '📉 散点图', 'value': 'scatter'}
                                ],
                                value='line',
                                clearable=False
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("选择数据类别:"),
                            dcc.Dropdown(
                                id='category-dropdown',
                                options=[
                                    {'label': '全部', 'value': 'all'},
                                    {'label': '类别 A', 'value': 'A'},
                                    {'label': '类别 B', 'value': 'B'},
                                    {'label': '类别 C', 'value': 'C'}
                                ],
                                value='all',
                                clearable=False
                            )
                        ], width=6)
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("日期范围:"),
                            dcc.DatePickerRange(
                                id='date-picker-range',
                                start_date=df['date'].min(),
                                end_date=df['date'].max(),
                                display_format='YYYY-MM-DD'
                            )
                        ], width=6),
                        dbc.Col([
                            dbc.Label("数据点数量:"),
                            dcc.Slider(
                                id='data-points-slider',
                                min=10,
                                max=100,
                                step=10,
                                value=50,
                                marks={i: str(i) for i in range(10, 101, 20)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=6)
                    ])
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # 多线程控制面板
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔄 多线程任务控制"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("▶️ 启动后台任务", id="start-btn", color="success", n_clicks=0),
                                dbc.Button("⏹️ 停止后台任务", id="stop-btn", color="danger", n_clicks=0)
                            ])
                        ], width=6),
                        dbc.Col([
                            html.Div(id="thread-status", className="mt-2")
                        ], width=6)
                    ]),
                    html.Hr(),
                    html.Div(id="real-time-data")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # 图表展示区域
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 数据可视化"),
                dbc.CardBody([
                    dcc.Graph(id='main-chart')
                ])
            ])
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📋 统计信息"),
                dbc.CardBody([
                    html.Div(id='stats-display')
                ])
            ])
        ], width=4)
    ], className="mb-4"),
    
    # 数据表格
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📄 数据表格"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='data-table',
                        columns=[
                            {"name": "日期", "id": "date", "type": "datetime"},
                            {"name": "销售额", "id": "sales", "type": "numeric", "format": {"specifier": ",.0f"}},
                            {"name": "利润", "id": "profit", "type": "numeric", "format": {"specifier": ",.2f"}},
                            {"name": "类别", "id": "category"}
                        ],
                        data=df.head(10).to_dict('records'),
                        page_size=10,
                        sort_action="native",
                        filter_action="native",
                        style_cell={'textAlign': 'left'},
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        }
                    )
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # 实时更新组件
    dcc.Interval(
        id='interval-component',
        interval=2*1000,  # 每2秒更新一次
        n_intervals=0
    )
], fluid=True)

# 回调函数：更新主图表
@app.callback(
    Output('main-chart', 'figure'),
    [Input('chart-type-dropdown', 'value'),
     Input('category-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('data-points-slider', 'value')]
)
def update_main_chart(chart_type, category, start_date, end_date, data_points):
    # 过滤数据
    filtered_df = df.copy()
    
    if category != 'all':
        filtered_df = filtered_df[filtered_df['category'] == category]
    
    if start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df['date'] >= start_date) & 
            (filtered_df['date'] <= end_date)
        ]
    
    # 限制数据点数量
    if len(filtered_df) > data_points:
        filtered_df = filtered_df.sample(n=data_points).sort_values('date')
    
    # 根据图表类型创建图表
    if chart_type == 'line':
        fig = px.line(filtered_df, x='date', y='sales', 
                     title='销售趋势图', color='category')
    elif chart_type == 'bar':
        fig = px.bar(filtered_df.groupby('category')['sales'].sum().reset_index(), 
                    x='category', y='sales', title='各类别销售额')
    elif chart_type == 'pie':
        category_sales = filtered_df.groupby('category')['sales'].sum().reset_index()
        fig = px.pie(category_sales, values='sales', names='category', 
                    title='销售额分布')
    elif chart_type == 'scatter':
        fig = px.scatter(filtered_df, x='sales', y='profit', 
                        color='category', title='销售额 vs 利润')
    
    fig.update_layout(template='plotly_white')
    return fig

# 回调函数：更新统计信息
@app.callback(
    Output('stats-display', 'children'),
    [Input('category-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_stats(category, start_date, end_date):
    # 过滤数据
    filtered_df = df.copy()
    
    if category != 'all':
        filtered_df = filtered_df[filtered_df['category'] == category]
    
    if start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df['date'] >= start_date) & 
            (filtered_df['date'] <= end_date)
        ]
    
    # 计算统计信息
    total_sales = filtered_df['sales'].sum()
    avg_sales = filtered_df['sales'].mean()
    total_profit = filtered_df['profit'].sum()
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    return [
        dbc.ListGroup([
            dbc.ListGroupItem([
                html.H5("💰 总销售额", className="mb-1"),
                html.P(f"¥{total_sales:,.0f}", className="mb-1 text-success")
            ]),
            dbc.ListGroupItem([
                html.H5("📊 平均销售额", className="mb-1"),
                html.P(f"¥{avg_sales:,.0f}", className="mb-1 text-info")
            ]),
            dbc.ListGroupItem([
                html.H5("💎 总利润", className="mb-1"),
                html.P(f"¥{total_profit:,.0f}", className="mb-1 text-warning")
            ]),
            dbc.ListGroupItem([
                html.H5("📈 利润率", className="mb-1"),
                html.P(f"{profit_margin:.1f}%", className="mb-1 text-primary")
            ])
        ])
    ]

# 回调函数：多线程控制
@app.callback(
    [Output('thread-status', 'children'),
     Output('start-btn', 'disabled'),
     Output('stop-btn', 'disabled')],
    [Input('start-btn', 'n_clicks'),
     Input('stop-btn', 'n_clicks')]
)
def control_background_task(start_clicks, stop_clicks):
    global background_running, background_thread
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return "🔴 未启动", False, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'start-btn' and not background_running:
        background_running = True
        background_thread = threading.Thread(target=background_task, daemon=True)
        background_thread.start()
        return "🟢 运行中", True, False
    
    elif button_id == 'stop-btn' and background_running:
        background_running = False
        if background_thread:
            background_thread.join(timeout=1)
        return "🔴 已停止", False, True
    
    # 返回当前状态
    if background_running:
        return "🟢 运行中", True, False
    else:
        return "🔴 已停止", False, True

# 回调函数：实时数据更新
@app.callback(
    Output('real-time-data', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_real_time_data(n):
    if data_queue.empty():
        return html.P("等待数据...", className="text-muted")
    
    # 获取最新的几条数据
    recent_data = []
    while not data_queue.empty() and len(recent_data) < 5:
        try:
            recent_data.append(data_queue.get_nowait())
        except queue.Empty:
            break
    
    if not recent_data:
        return html.P("暂无数据", className="text-muted")
    
    # 显示最新数据
    data_items = []
    for data in reversed(recent_data[-5:]):  # 显示最新的5条
        data_items.append(
            dbc.Alert([
                html.Strong(f"⏰ {data['time']} "),
                f"数值: {data['value']} | 状态: {data['status']}"
            ], color="info", className="mb-1")
        )
    
    return data_items

if __name__ == '__main__':
    print("🚀 启动Dash应用...")
    print("📱 访问地址: http://127.0.0.1:8050")
    app.run(debug=True, host='127.0.0.1', port=8050)