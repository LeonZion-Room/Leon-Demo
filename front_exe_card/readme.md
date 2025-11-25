# 背景
- 我是一个 Python 程序员

# 具体需求
- 我是希望有个网页，可以有网格，可以拖动设置组件布局，组件是输入一个网页，展示对应内容，允许鼠标交互


# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 我已经预先安装好了环境：.venv\Scripts\python.exe
- 我希望你用 .venv 的相对路径进行环境的激活,如 下载库使用 .venv\Scripts\pip install  xxxxxx；运行软件使用.venv\Scripts\python main.py 运行软件
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/



.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --name CardGrid --windowed --add-data "pyside_exe_card\data\layout.json;pyside_exe_card\data" --onefile  pyside_exe_card\app.py