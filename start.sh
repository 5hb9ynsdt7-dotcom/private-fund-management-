#!/bin/bash

# Private Fund 项目智能启动脚本
# 自动检测并处理端口冲突

echo "🚀 正在启动 Private Fund 项目..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 杀死占用端口的进程
kill_port() {
    local port=$1
    echo -e "${YELLOW}⚠️  端口 $port 被占用${NC}"

    # 获取占用端口的进程信息
    local pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        local process_name=$(ps -p $pid -o comm=)
        echo "   占用进程: $process_name (PID: $pid)"

        # 询问用户是否要杀死进程
        read -p "   是否要停止该进程？(y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill -9 $pid
            echo -e "${GREEN}✅ 已停止进程 $pid${NC}"
            sleep 1
            return 0
        else
            echo -e "${RED}❌ 用户取消操作${NC}"
            return 1
        fi
    fi
}

# 检查后端端口 (8000)
echo "📡 检查后端端口 8000..."
if check_port 8000; then
    if ! kill_port 8000; then
        echo -e "${RED}❌ 无法启动后端服务，端口 8000 被占用${NC}"
        echo "   请手动停止占用端口的进程，或修改后端端口配置"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 端口 8000 可用${NC}"
fi

echo ""

# 检查 pm2 是否安装
if ! command -v pm2 &> /dev/null; then
    echo -e "${RED}❌ pm2 未安装${NC}"
    echo "   正在安装 pm2..."
    sudo npm install -g pm2
fi

# 停止之前的 pm2 进程
echo "🛑 停止之前的服务..."
pm2 delete all 2>/dev/null

echo ""

# 启动服务
echo "🎬 启动前后端服务..."
pm2 start ecosystem.config.js

echo ""

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

echo ""

# 检查服务状态
echo "📊 服务状态："
pm2 list

echo ""

# 检查后端健康状态
echo "🏥 检查后端健康状态..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ 后端服务正常运行 (http://localhost:8000)${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    echo "   查看日志: pm2 logs privatefund-backend"
fi

echo ""

# 获取前端实际运行的端口
echo "🌐 检查前端服务..."
sleep 2
frontend_port=$(pm2 logs privatefund-frontend --nostream --lines 50 | grep -o "localhost:[0-9]*" | head -1 | cut -d: -f2)

if [ ! -z "$frontend_port" ]; then
    echo -e "${GREEN}✅ 前端服务正常运行 (http://localhost:$frontend_port)${NC}"
    echo ""
    echo "🎉 所有服务启动完成！"
    echo ""
    echo "📝 常用命令："
    echo "   查看日志: pm2 logs"
    echo "   停止服务: pm2 stop all"
    echo "   重启服务: pm2 restart all"
    echo "   查看状态: pm2 list"
    echo ""
    echo "🌍 访问地址："
    echo "   前端: http://localhost:$frontend_port"
    echo "   后端: http://localhost:8000"
    echo "   API文档: http://localhost:8000/docs"
else
    echo -e "${YELLOW}⚠️  前端服务可能还在启动中...${NC}"
    echo "   查看日志: pm2 logs privatefund-frontend"
fi

echo ""
