Param(
    [string]$Mirror = "https://mirrors.aliyun.com/pypi/simple/"
)

# 在项目根目录下创建虚拟环境（若不存在）
if (-not (Test-Path ".venv")) {
    Write-Host "创建虚拟环境 .venv..." -ForegroundColor Cyan
    try {
        py -m venv .venv
    } catch {
        Write-Host "py 不可用，尝试使用 python" -ForegroundColor Yellow
        python -m venv .venv
    }
}

# 安装依赖（使用阿里云镜像）
Write-Host "安装依赖 PySide6..." -ForegroundColor Cyan
& .\.venv\Scripts\pip.exe install -i $Mirror PySide6 | Out-Host

# 启动应用
Write-Host "启动应用..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe .\app.py