# 使用官方的Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装Node.js 20
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装前端依赖并构建
WORKDIR /app/frontend
RUN npm install && npm run build

# 安装后端依赖
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# 设置工作目录为后端
WORKDIR /app/backend

# 暴露端口
EXPOSE $PORT

# 启动命令
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT