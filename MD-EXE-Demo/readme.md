#工具/AI-提示词
> Coding
# 背景

- 我是一个 Python 程序员
- 我希望尽量简单的代码实现一个windows的软件功能


# 具体需求
- 希望完成一个输入markdown并实时渲染的功能
- 希望文件保存在最靠近的目录下，与exe文件在同一目录
- 希望可以在有边框的前提下用鼠标调整大小，没边框的时候无法修改
- 希望可以自动记录最新的窗口尺寸和位置，默认在启动时加载上次记录的位置


# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 不要去寻找python环境，直接使用相对路径下指定的应用去执行操作，下载库必须使用 .venv/Scripts/pip install xxx,运行时必须使用 .venv/Scripts/python 或 .venv/Scripts/streamlit run
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/

## 使用说明（PowerShell）
- 在项目根目录执行：
- `powershell -ExecutionPolicy Bypass -File .\run.ps1`
- 脚本会自动：
- 1) 在当前目录创建 `.venv` 虚拟环境（如不存在）
- 2) 通过阿里云镜像安装 `PySide6`
- 3) 使用 `.venv\Scripts\python` 启动 `app.py`

## 应用功能说明
- 左侧输入 Markdown，右侧实时预览
- 点击“保存到同目录”将内容保存到与 exe/脚本同目录的 `document.md`
- 点击“另存为”可自选保存路径（默认定位到同目录）
- 点击“切换边框”可在有边框/无边框间切换：
- 有边框：可用鼠标自由调整窗口大小
- 无边框：窗口尺寸被锁定，鼠标无法调整（满足“没边框时无法修改”）
- 自动记录窗口尺寸与位置，在 `md_exe_config.json` 中保存，启动时自动恢复

## 新增特性
- 自动保存：输入时每 1 秒防抖自动保存到同目录 `document.md`
- 默认置底：窗口默认设置为底层显示（尽量保持在其他窗口下方）
 - 文件管理：
 - 应用启动自动创建同目录 `files/`
 - 支持拖拽文件到窗口，自动复制到 `files/`
 - 左侧列表显示 `files/` 内文件，点击文件名：
 - Markdown (`.md/.markdown`) 将在编辑区打开并预览
 - 其他类型使用系统默认程序打开
- 顶部按钮：
- “打开files目录”打开资源管理器定位到 `files/`
- “清空files”删除 `files/` 下所有文件/子目录
 - “重命名”对选中文件进行重命名，自动避免同名覆盖

## 文件面板位置与展示
- 文件面板已移动到编辑器与预览的下方（底部），通过上下分割可调整高度
- 列表以图标模式展示，图标更大、更醒目；Markdown 文件名加粗显示

