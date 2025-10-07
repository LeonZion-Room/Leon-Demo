# Nginx 反向代理配置使用说明

## 功能概述
通过nginx反向代理，将一个公网IP端口通过不同的URL路径分发到不同的本地端口，实现端口扩展功能。

## 配置说明

### 路由映射表
| URL路径 | 本地端口 | 用途示例 |
|---------|----------|----------|
| `/app1/` | 3000 | React/Vue前端应用 |
| `/api/` | 8080 | Spring Boot后端API |
| `/web/` | 5000 | Python Flask/Django应用 |
| `/node/` | 9000 | Node.js应用 |
| `/redis/` | 6379 | Redis管理界面 |
| `/files/` | 8000 | 文件服务器 |
| `/health` | - | 健康检查端点 |

### 访问示例
假设您的公网IP是 `123.456.789.0`，端口映射到本地的80端口：

- 访问前端应用：`http://123.456.789.0/app1/`
- 访问API接口：`http://123.456.789.0/api/users`
- 访问Web应用：`http://123.456.789.0/web/dashboard`
- 访问Node.js应用：`http://123.456.789.0/node/`
- 访问文件服务：`http://123.456.789.0/files/download/file.pdf`
- 健康检查：`http://123.456.789.0/health`

## 启动和管理

### 启动nginx
```powershell
cd "C:\Users\leonz\Desktop\Codings\Leon-Demo\nginx-Demo\nginx-1.25.3"
.\nginx.exe
```

### 重新加载配置
```powershell
.\nginx.exe -s reload
```

### 停止nginx
```powershell
.\nginx.exe -s stop
```

### 验证配置
```powershell
.\nginx.exe -t
```

## 配置特性

### 1. 请求头转发
所有代理请求都会转发以下重要的HTTP头：
- `Host`: 原始主机名
- `X-Real-IP`: 客户端真实IP
- `X-Forwarded-For`: 代理链IP
- `X-Forwarded-Proto`: 原始协议(http/https)

### 2. WebSocket支持
`/app1/` 路径支持WebSocket连接，适用于实时应用。

### 3. 超时设置
API路径(`/api/`)配置了30秒的连接、发送和读取超时。

### 4. 文件上传
文件服务路径(`/files/`)支持最大100MB的文件上传。

### 5. 安全设置
- 拒绝访问隐藏文件（以`.`开头的文件）
- 健康检查端点不记录访问日志

## 自定义配置

### 添加新的服务
要添加新的服务路由，在server块中添加新的location配置：

```nginx
# 新服务 - 代理到本地端口XXXX
location /newservice/ {
    proxy_pass http://127.0.0.1:XXXX/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### 修改端口映射
要修改现有服务的端口，只需更改对应location块中的`proxy_pass`地址。

## 故障排除

### 1. 检查nginx状态
```powershell
# 查看nginx进程
Get-Process nginx

# 查看端口占用
netstat -ano | findstr :80
```

### 2. 查看日志
- 错误日志：`logs/error.log`
- 访问日志：`logs/access.log`

### 3. 常见问题
- **502 Bad Gateway**: 目标服务未启动或端口错误
- **404 Not Found**: URL路径配置错误
- **连接超时**: 目标服务响应慢或网络问题

## 注意事项

1. 确保目标端口的服务已启动
2. 防火墙需要允许相应端口的访问
3. 如果使用HTTPS，需要配置SSL证书
4. 定期检查nginx和目标服务的运行状态
5. 根据实际需求调整超时和缓冲区设置