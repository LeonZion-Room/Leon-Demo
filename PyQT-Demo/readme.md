# 背景
- 我是一个 Python 程序员

## LZ-PDF 转 DOCX 图形界面

本项目已新增 `main.py`，使用 PyQt6 构建无边框窗口，实现如下功能：
- 上传 PDF 文件
- 选择输出路径（或默认同名）
- 开始转换（进度条实时更新）
- 打开生成的 DOCX
- 联系我们（打开指定网址，默认 `https://www.example.com/`，可在 `main.py` 修改 `CONTACT_URL`）

### 运行环境准备（Windows / PowerShell）

1. 如果还没有虚拟环境，建议创建：
   ```powershell
   py -m venv .venv
   ```

2. 安装依赖（全部使用阿里云镜像）：
   ```powershell
   .\.venv\Scripts\pip install -i https://mirrors.aliyun.com/pypi/simple/ PyQt6 comtypes
   ```
   - `comtypes` 用于与 Word 的 COM 交互，`pdf_fc.py` 内也内置了缺库自动安装逻辑（同样走阿里云镜像）。

3. 启动应用：
   ```powershell
   .\.venv\Scripts\python main.py
   ```

> 说明：转换依赖本机安装 Microsoft Word；若未安装或 Word 无法启动，将无法转换。

# 具体需求
- 希望能完成一个 windows的应用，参考example.py和pdf_fc.py进行改写来实现需求



# 开发细节
- 我的开发环境是 windows11，尽量使用powershell进行操作
- 我希望你用 .venv 的相对路径进行环境的激活,如 下载库使用 .venv\Scripts\pip install  xxxxxx；运行软件使用.venv\Scripts\python main.py 运行软件
- 希望所有 Pip install 使用阿里云镜像- https://mirrors.aliyun.com/pypi/simple/

