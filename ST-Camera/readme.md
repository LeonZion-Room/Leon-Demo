# 背景
- 我是一个 Python 程序员

# 具体需求
- 希望能完成一个 基于streamlit 和其第三方组建的 拍照系统
- 希望能基于这个系统，实现拍照并保存，存储为jpg格式，并提供下载按钮
- 希望能加上一个 opencv 模型，用于人脸识别并给出下载人脸jpg的按钮



# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 我希望你用 .venv 的相对路径进行环境的激活,如 下载库使用 .venv\Scripts\pip install  xxxxxx；运行软件使用.venv\Scripts\python main.py 运行软件
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/

---

# 安装与运行
- 使用 PowerShell 在项目根目录执行以下命令：

1) 创建虚拟环境（.venv）
- `python -m venv .venv`

2) 安装依赖（使用阿里云镜像）
- `.venv\Scripts\pip install -i https://mirrors.aliyun.com/pypi/simple/ streamlit streamlit-webrtc opencv-python av`

3) 启动应用（通过 Python 脚本）
- `.venv\Scripts\python main.py`

# 功能说明
- 拍照并保存：使用 `st.camera_input` 进行抓拍，自动保存为 JPG，并提供下载按钮。
- 人脸检测与裁剪：使用 OpenCV Haar 模型检测人脸，展示框图；将每张人脸裁剪为 JPG 并提供下载按钮；文件保存到 `faces/`。
- 第三方组件实时预览：集成 `streamlit-webrtc` 实时预览摄像头画面，并叠加人脸检测框（抓拍与下载在“拍照并下载”页进行）。

# 目录说明
- `main.py`：启动脚本，支持通过 `.venv\Scripts\python main.py` 运行。
- `app.py`：Streamlit 应用主体。
- `captures/`：保存抓拍原图（运行时自动创建）。
- `faces/`：保存裁剪后的人脸图片（运行时自动创建）。