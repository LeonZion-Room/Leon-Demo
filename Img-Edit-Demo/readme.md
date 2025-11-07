# 背景
- 我是一个 Python 程序员

# 具体需求
- 希望能完成一个 图片编辑系统
- 可以上传图片，基于 opencv 获取人脸截图切片，直接下载
- 也可以在人脸截图基础上调整坐标和大小，进行二次编辑于下载
- 基于 streamlit 实现


# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 我希望你用 .venv 的相对路径进行环境的激活,如 下载库使用 .venv\Scripts\pip install  xxxxxx；运行软件使用.venv\Scripts\python main.py 运行软件
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/


---

# 使用指南（Windows 11 + PowerShell）

- 创建虚拟环境：
  - `py -m venv .venv`

- 安装依赖（使用阿里云镜像）：
  - `.venv\Scripts\pip install --index-url https://mirrors.aliyun.com/pypi/simple/ streamlit opencv-python pillow numpy`

- 运行应用（使用相对路径的 Python 解释器）：
  - `.venv\Scripts\python main.py`

运行后浏览器会自动打开（或在终端提示 `Local URL: http://localhost:8501`），上传图片即可进行人脸检测与二次编辑裁剪并下载。

