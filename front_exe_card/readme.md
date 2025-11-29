# 背景
- 我是一个 Python 程序员

# 具体需求
- 我是希望有个网页，可以有网格，可以拖动设置组件布局，组件是输入一个网页，展示对应内容，允许鼠标交互


# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 我已经预先安装好了环境：.venv\Scripts\python.exe
- 我希望你用 .venv 的相对路径进行环境的激活,如 下载库使用 .venv\Scripts\pip install  xxxxxx；运行软件使用.venv\Scripts\python main.py 运行软件
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/

- 希望一个桌面应用组件只能展示一个应用，然后展示的时候会自动缩放贴合，允许调整展示比例
- 我感觉不要将桌面应用的绑定太死，比如说我这次绑定一个应用，它叫做 “test.py sublimetext”,下次如果 是“xxx-sublimetext”，我也希望它可以展示出来,希望能够模糊匹配，如果出现多个满足情况的窗口再让用户从多个选择中选出指定的
- 我发现桌面应用组件里的展示没有自动和组件尺寸贴合，我希望能贴合并调整桌面应用组件内部应用的展示大小；而且希望如果加入了一个应用，又把他删除后，这个应用能恢复原来的样子
- 希望桌面应用组件的能添加一个按钮，用于让内部应用尺寸自动适配组件尺寸
- 我希望桌面应用调整比例的是应用整体的缩放比例而不是尺寸
- 我发现删除组建后回复的应用展示不正常
- 删除掉桌面组件的放缩滑杆，并删除相关功能
- 希望对桌面组件的目标应用修改后，原应用会被释放出去
- 希望桌面应用组件的能添加一个按钮，用于让内部应用尺寸自动适配组件尺寸，自动填满组件容器
- 桌面应用部件显示异常
- 我发现会影响到我原有的系统桌面，造成异常  希望你能在筛选的地方排除那些会造成系统异常的窗口，并避免这样得情况发生

.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --name CardGrid --windowed --add-data "pyside_exe_card\data\layout.json;pyside_exe_card\data" --onefile  pyside_exe_card\app.py