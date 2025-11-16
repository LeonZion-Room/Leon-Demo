#中转
<#
.SYNOPSIS
终极稳定版：永不自动退出 + 强制管理员权限 + 重置网络配置 + 重启有线网络
核心：任何情况都不自动关闭窗口，需手动点击右上角关闭
#>

# ==============================================
# 第一步：权限处理（优先自动申请，失败则提示手动操作，不退出）
# ==============================================
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`n⚠️  未获取管理员权限，正在尝试自动申请..." -ForegroundColor Yellow
    try {
        # 自动申请管理员权限（修复路径空格问题）
        $scriptPath = [System.IO.Path]::GetFullPath($MyInvocation.MyCommand.Definition)
        $escapedPath = "`"$scriptPath`""
        Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File $escapedPath" -Verb RunAs -NoNewWindow
        Write-Host "✅ 已弹出权限申请窗口，请点击「是」继续..." -ForegroundColor Green
        # 不退出当前窗口，让用户看到提示（直到手动关闭）
        Write-Host "`n⚠️  若未弹出权限窗口，请右键脚本 → 以管理员身份运行！" -ForegroundColor Red
        Write-Host "`n窗口将保持打开，需手动关闭..." -ForegroundColor Gray
        Read-Host -Prompt "`n按任意键查看详细说明（或直接关闭窗口）"
        Write-Host "`n详细说明："
        Write-Host "1. 脚本需要管理员权限才能修改网络配置"
        Write-Host "2. 若自动申请失败，手动右键脚本 → 以管理员身份运行"
        Write-Host "3. 操作完成后，可直接关闭窗口"
        # 无限等待，不退出
        while ($true) { Start-Sleep -Seconds 3600 }
    }
    catch {
        Write-Host "`n❌ 自动申请权限失败！" -ForegroundColor Red
        Write-Host "`n请手动操作：" -ForegroundColor Green
        Write-Host "1. 右键点击本脚本文件"
        Write-Host "2. 选择「以管理员身份运行」"
        Write-Host "`n窗口将保持打开，按任意键可重复查看说明..." -ForegroundColor Gray
        # 无限循环，不退出
        while ($true) {
            Read-Host -Prompt "`n按任意键查看操作步骤"
            Write-Host "`n手动获取管理员权限步骤："
            Write-Host "1. 右键脚本 → 以管理员身份运行"
            Write-Host "2. 弹出UAC窗口 → 点击「是」"
        }
    }
}

# ==============================================
# 第二步：全局配置（强制不退出，捕获所有错误）
# ==============================================
Write-Host "`n===== 已获取管理员权限，开始执行网络配置重置 =====" -ForegroundColor Green
Write-Host "⚠️  重要提示：本窗口不会自动退出，操作完成后需手动关闭！`n" -ForegroundColor Yellow

# 捕获所有错误（即使出错也不退出，仅显示错误）
trap {
    Write-Host "`n❌ 某步骤执行出错：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host "✅ 窗口继续保持打开，不影响后续操作！`n" -ForegroundColor Green
    # 不退出，继续执行后续步骤
    Continue
}

# ==============================================
# 第三步：清除手动网络配置，改为自动获取（DHCP）
# ==============================================
Write-Host "`n===== 1. 正在清除手动网络配置，改为自动获取 =====" -ForegroundColor Cyan
try {
    # 简化接口获取逻辑（减少过滤，避免识别失败导致闪退）
    $allInterfaces = Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object {
        $_.Status -in "Up", "Down"  # 只过滤无效接口
        -and $_.MacAddress -notmatch "00-00-00-00-00-00"  # 排除无效MAC
    }

    if ($allInterfaces.Count -eq 0) {
        Write-Host "`n⚠️  未找到有效网络接口（可能网线未插或网卡异常）" -ForegroundColor Yellow
    } else {
        Write-Host "`n找到 $($allInterfaces.Count) 个有效网络接口：" -ForegroundColor Green
        $allInterfaces | ForEach-Object { Write-Host " - $($_.Name)（状态：$($_.Status)）" }

        foreach ($adapter in $allInterfaces) {
            $interfaceName = $adapter.Name
            Write-Host "`n🔧 处理接口：$interfaceName" -ForegroundColor Cyan

            # 重置IPv4（核心操作）
            try {
                Set-NetIPInterface -InterfaceAlias $interfaceName -AddressFamily IPv4 -Dhcp Enabled -ErrorAction Stop
                Remove-NetIPAddress -InterfaceAlias $interfaceName -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
                Remove-NetRoute -InterfaceAlias $interfaceName -AddressFamily IPv4 -Confirm:$false -ErrorAction SilentlyContinue
                Set-DnsClientServerAddress -InterfaceAlias $interfaceName -AddressFamily IPv4 -ServerAddresses @() -ErrorAction Stop
                Write-Host "✅ IPv4：已改为自动获取" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ IPv4重置失败（非致命）：$($_.Exception.Message)" -ForegroundColor DarkYellow
            }

            # 重置IPv6（可选）
            try {
                Set-NetIPInterface -InterfaceAlias $interfaceName -AddressFamily IPv6 -Dhcp Enabled -ErrorAction Stop
                Set-DnsClientServerAddress -InterfaceAlias $interfaceName -AddressFamily IPv6 -ServerAddresses @() -ErrorAction Stop
                Write-Host "✅ IPv6：已改为自动获取" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ IPv6重置失败（忽略）：$($_.Exception.Message)" -ForegroundColor DarkYellow
            }
        }
    }
}
catch {
    Write-Host "`n❌ 网络配置重置步骤出错：$($_.Exception.Message)" -ForegroundColor Red
}

# ==============================================
# 第四步：断开并重新连接有线网络
# ==============================================
Write-Host "`n`n===== 2. 正在重启有线网络连接 =====" -ForegroundColor Cyan
try {
    $wiredInterfaces = Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object {
        $_.InterfaceType -eq 6  # 仅保留以太网（有线）
        -and $_.Status -in "Up", "Down"
        -and $_.Name -notmatch "虚拟|VPN|无线|Wi-Fi"
    }

    if ($wiredInterfaces.Count -eq 0) {
        Write-Host "`n⚠️  未找到有线网络接口（检查网线是否插好）" -ForegroundColor Yellow
    } else {
        Write-Host "`n找到 $($wiredInterfaces.Count) 个有线接口：" -ForegroundColor Green
        $wiredInterfaces | ForEach-Object { Write-Host " - $($_.Name)（状态：$($_.Status)）" }

        # 断开有线连接
        Write-Host "`n正在断开有线连接..." -ForegroundColor Cyan
        foreach ($adapter in $wiredInterfaces) {
            try {
                Disable-NetAdapter -Name $adapter.Name -Confirm:$false -ErrorAction Stop -NoRestart
                Write-Host "✅ 已断开：$($adapter.Name)" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ 断开失败：$($_.Exception.Message)" -ForegroundColor Red
            }
        }

        # 等待3秒
        Write-Host "`n等待3秒后重新连接..." -ForegroundColor Gray
        Start-Sleep -Seconds 3

        # 重新连接
        Write-Host "`n正在重新连接有线连接..." -ForegroundColor Cyan
        foreach ($adapter in $wiredInterfaces) {
            try {
                Enable-NetAdapter -Name $adapter.Name -Confirm:$false -ErrorAction Stop -NoRestart
                Write-Host "✅ 已连接：$($adapter.Name)" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ 连接失败：$($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}
catch {
    Write-Host "`n❌ 有线网络重启步骤出错：$($_.Exception.Message)" -ForegroundColor Red
}

# ==============================================
# 第五步：强制常驻窗口（永不自动退出）
# ==============================================
Write-Host "`n`n===== 所有操作执行完毕！=====" -ForegroundColor Green
Write-Host "✅ 已完成：" -ForegroundColor Green
Write-Host "1. 确认管理员权限"
Write-Host "2. 清除所有手动网络配置，改为自动获取"
Write-Host "3. 重启所有有线网络连接"
Write-Host "`n⚠️  重要：本窗口不会自动关闭！" -ForegroundColor Yellow
Write-Host "操作：" -ForegroundColor Gray
Write-Host "1. 检查网络是否恢复正常"
Write-Host "2. 确认无误后，手动点击窗口右上角「×」关闭"
Write-Host "3. 若有错误提示，可截图发送用于排查"

# 无限循环，强制窗口常驻（除非手动关闭）
while ($true) {
    Start-Sleep -Seconds 3600  # 每小时循环一次，不占用资源
}