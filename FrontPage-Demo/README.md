# 个人介绍页面

一个基于 Flask、HTML、CSS 和 JavaScript 构建的现代化个人介绍页面。支持通过命令行参数自定义端口和页面名称。

## 功能特点

- 🎨 现代化响应式设计
- 📱 移动端友好
- ⚡ 流畅的动画效果
- 🎯 平滑滚动导航
- 📧 联系表单
- 🔧 命令行参数配置
- 🌐 跨平台支持

## 项目结构

```
FrontPage-Demo/
├── app.py                 # Flask 应用主文件
├── requirements.txt       # Python 依赖
├── README.md             # 项目说明
├── templates/            # HTML 模板
│   └── index.html        # 主页模板
└── static/               # 静态资源
    ├── css/
    │   └── style.css     # 样式文件
    └── js/
        └── script.js     # JavaScript 文件
```

## 安装和运行

### 1. 克隆或下载项目

```bash
git clone <repository-url>
cd FrontPage-Demo
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用

#### 基本运行（默认配置）
```bash
python app.py
```
- 默认端口：5000
- 默认名称：个人介绍页面
- 访问地址：http://localhost:5000

#### 自定义端口
```bash
python app.py -p 8080
```
或
```bash
python app.py --port 8080
```

#### 自定义页面名称
```bash
python app.py -n "我的个人网站"
```
或
```bash
python app.py --name "我的个人网站"
```

#### 同时自定义端口和名称
```bash
python app.py -p 8080 -n "我的个人网站"
```

#### 启用调试模式
```bash
python app.py --debug
```

#### 查看帮助信息
```bash
python app.py -h
```

## 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--port` | `-p` | 指定服务器端口 | 5000 |
| `--name` | `-n` | 指定页面名称 | 个人介绍页面 |
| `--debug` | - | 启用调试模式 | False |
| `--help` | `-h` | 显示帮助信息 | - |

## 页面功能

### 导航栏
- 响应式设计，支持移动端汉堡菜单
- 平滑滚动到对应部分
- 滚动时高亮当前部分

### 主页部分
- 欢迎信息展示
- 个人简介卡片
- 行动按钮

### 关于我部分
- 个人介绍
- 统计数据展示
- 技能特色卡片

### 技能部分
- 技能卡片展示
- 进度条动画
- 图标和描述

### 联系方式部分
- 联系信息展示
- 交互式联系表单
- 表单验证和提交反馈

### 其他功能
- 返回顶部按钮
- 页面滚动动画
- 响应式布局
- 社交媒体链接

## 自定义配置

### 修改页面内容
编辑 `templates/index.html` 文件来修改页面内容：
- 个人信息
- 技能列表
- 联系方式
- 社交媒体链接

### 修改样式
编辑 `static/css/style.css` 文件来自定义：
- 颜色主题
- 字体样式
- 布局设计
- 动画效果

### 修改交互功能
编辑 `static/js/script.js` 文件来：
- 添加新的交互功能
- 修改动画效果
- 自定义表单处理

## API 接口

应用提供了一个简单的 API 接口：

### GET /api/info
返回应用的基本信息

**响应示例：**
```json
{
    "name": "个人介绍页面",
    "port": 5000,
    "status": "running"
}
```

## 技术栈

- **后端**: Flask (Python)
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **图标**: Font Awesome
- **字体**: Segoe UI 系列

## 浏览器支持

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 开发说明

### 开发模式运行
```bash
python app.py --debug
```

### 代码结构说明
- `app.py`: Flask 应用主文件，处理路由和命令行参数
- `templates/index.html`: 主页模板，使用 Jinja2 模板引擎
- `static/css/style.css`: 样式文件，使用 CSS3 特性和变量
- `static/js/script.js`: JavaScript 文件，处理页面交互和动画

### 添加新功能
1. 在 HTML 中添加新的结构
2. 在 CSS 中添加对应的样式
3. 在 JavaScript 中添加交互逻辑
4. 如需后端支持，在 Flask 中添加新路由

## 部署说明

### 本地部署
按照上述安装和运行步骤即可。

### 生产环境部署
建议使用 Gunicorn 或 uWSGI 等 WSGI 服务器：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 许可证

本项目采用 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱：example@email.com
- GitHub：github.com/username

---

**享受使用这个个人介绍页面！** 🎉