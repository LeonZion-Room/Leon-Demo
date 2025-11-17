# 视频存储和流媒体平台部署说明

## 项目概述
本项目是一个基于 FastAPI 实现的视频存储和流媒体平台，支持视频上传、压缩、预览和流媒体播放功能。

## 部署环境
- Python 3.10+
- Windows 11 (使用 PowerShell)
- FFmpeg (通过 imageio-ffmpeg 自动安装)

## 部署步骤

### 1. 创建虚拟环境
```powershell
cd c:\Users\leonz\Desktop\WorkSpace\Leon-Demo\api_movie
python -m venv .venv
```

### 2. 激活虚拟环境
```powershell
.venv\Scripts\Activate.ps1
```

### 3. 安装依赖包
```powershell
.venv\Scripts\pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 4. 创建数据目录结构
```powershell
mkdir data\original
mkdir data\compressed
mkdir data\tmp
mkdir data\tmp_preview
```

### 5. 启动服务
```powershell
.venv\Scripts\python main.py
```

服务将在 `http://localhost:8001` 上运行。

## 使用说明

### 访问平台
打开浏览器访问 `http://localhost:8001` 即可进入视频管理平台。

### 功能介绍
1. **视频上传**：
   - 选择视频文件
   - 设置压缩指数 (CRF 18-32，数值越小质量越高)
   - 可选择生成预览或直接上传

2. **预览功能**：
   - 点击"生成预览"按钮可生成约5秒的预览视频
   - 预览满意后点击"提交上传"完成上传

3. **视频管理**：
   - 查看所有上传的视频
   - 播放原始视频和压缩视频
   - 查看视频信息（大小、时长等）
   - 重命名和删除视频

### API 接口
- `GET /` - 主页
- `GET /videos` - 获取所有视频列表
- `POST /preview` - 生成预览视频
- `POST /commit` - 提交预览视频到正式存储
- `POST /upload` - 直接上传视频
- `GET /stream/original/{id}` - 流媒体播放原始视频
- `GET /stream/compressed/{id}` - 流媒体播放压缩视频
- `GET /view/original/{id}` - 全屏播放原始视频
- `GET /view/compressed/{id}` - 全屏播放压缩视频

## 注意事项
1. 请确保端口 8000 未被其他程序占用
2. 视频文件存储在 `data/original` 和 `data/compressed` 目录中
3. 临时文件存储在 `data/tmp` 和 `data/tmp_preview` 目录中
4. 视频信息存储在 `data/videos.json` 文件中