# Private Fund 项目启动指南

## 快速启动

### 方式一：使用智能启动脚本（推荐）

```bash
./start.sh
```

这个脚本会：
- ✅ 自动检测端口冲突
- ✅ 询问你是否要停止占用端口的进程
- ✅ 启动前后端服务
- ✅ 显示服务运行状态和访问地址

### 方式二：手动使用 pm2

```bash
pm2 start ecosystem.config.js
```

## 停止服务

### 方式一：使用停止脚本

```bash
./stop.sh
```

### 方式二：手动停止

```bash
pm2 stop all          # 停止所有服务
pm2 delete all        # 停止并删除所有服务
```

## 遇到端口冲突怎么办？

### 情况 1：后端端口 8000 被占用

**自动处理（推荐）：**
```bash
./start.sh
```
脚本会提示你是否要停止占用端口的进程。

**手动处理：**
```bash
# 1. 查看是什么占用了 8000 端口
lsof -i :8000

# 2. 停止占用端口的进程
kill -9 <进程ID>

# 3. 重新启动
pm2 restart privatefund-backend
```

### 情况 2：前端端口被占用

**不用担心！** 前端使用 Vite，会自动找到可用端口：
- 默认尝试 5173
- 如果被占用，自动尝试 5174, 5175...

启动后查看实际端口：
```bash
pm2 logs privatefund-frontend --lines 20
```

## 常用命令

### 查看服务状态
```bash
pm2 list              # 查看所有服务
pm2 status            # 同上
```

### 查看日志
```bash
pm2 logs                              # 查看所有日志
pm2 logs privatefund-backend          # 只看后端日志
pm2 logs privatefund-frontend         # 只看前端日志
pm2 logs --lines 100                  # 查看最近 100 行
```

### 重启服务
```bash
pm2 restart all                       # 重启所有服务
pm2 restart privatefund-backend       # 只重启后端
pm2 restart privatefund-frontend      # 只重启前端
```

### 停止服务
```bash
pm2 stop all                          # 停止所有服务
pm2 stop privatefund-backend          # 只停止后端
pm2 stop privatefund-frontend         # 只停止前端
```

### 删除服务
```bash
pm2 delete all                        # 删除所有服务
pm2 delete privatefund-backend        # 只删除后端
pm2 delete privatefund-frontend       # 只删除前端
```

## 服务访问地址

- **前端**: http://localhost:5173 (或其他自动分配的端口)
- **后端**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 日志文件位置

所有日志保存在 `logs/` 目录：
- `logs/backend-out.log` - 后端正常输出
- `logs/backend-error.log` - 后端错误日志
- `logs/frontend-out.log` - 前端正常输出
- `logs/frontend-error.log` - 前端错误日志

## 故障排查

### 1. 服务启动失败

```bash
# 查看详细日志
pm2 logs

# 查看特定服务的错误
pm2 logs privatefund-backend --err
```

### 2. 后端无法访问

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查端口是否被占用
lsof -i :8000

# 重启后端
pm2 restart privatefund-backend
```

### 3. 前端无法访问

```bash
# 查看前端实际运行的端口
pm2 logs privatefund-frontend --lines 20 | grep "Local:"

# 重启前端
pm2 restart privatefund-frontend
```

### 4. 完全重置

```bash
# 停止并删除所有服务
pm2 delete all

# 重新启动
./start.sh
```

## 开机自启动（可选）

如果你希望电脑重启后自动启动服务：

```bash
# 保存当前 pm2 进程列表
pm2 save

# 设置开机自启动
pm2 startup

# 按照提示执行命令（需要 sudo 权限）
```

## 注意事项

1. **后端端口固定为 8000**，如果被占用需要手动处理
2. **前端端口会自动选择**，不需要手动干预
3. **使用 `./start.sh` 最省心**，会自动处理端口冲突
4. **日志会持续增长**，定期清理 `logs/` 目录
5. **修改代码后**，后端会自动重载（--reload），前端会自动刷新（Vite HMR）

## 配置文件

- `ecosystem.config.js` - pm2 配置文件
- `start.sh` - 智能启动脚本
- `stop.sh` - 停止脚本

需要修改端口或其他配置，编辑 `ecosystem.config.js` 文件。
