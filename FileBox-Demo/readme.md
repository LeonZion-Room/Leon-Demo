# 背景
- 我是一个 Python 程序员

# 具体需求
- 希望能完成一个 基于 streamlit 的文件存储系统
- 希望尽量简洁，默认界面为上传界面，就是一个框可以拖动文件进去，也可以点击来选择文件，希望能一次设定多个文件
- 上传完成后会有个地方点击获得查看链接，即查看当次上传的文件，查看链接打开后是一个表格对应多个文件名称和下载按钮，表格处允许修改文件名称，对应的下载链接也会跟着改动
- 文件名字作为下载链接要注意不能包含url不接受的特殊字符，否则会导致下载链接失效
- 希望需要密码登录才能进行相关操作

# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 我希望你用 .venv 的相对路径进行环境的激活,如 下载库使用 .venv\Scripts\pip install  xxxxxx；运行软件使用.venv\Scripts\python main.py 运行软件
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/

---

- 基于 solo 模式完成
- 具体参数需要参考 config.json 可以 "auto" | "xx.xx.xx.xx" 确定网络