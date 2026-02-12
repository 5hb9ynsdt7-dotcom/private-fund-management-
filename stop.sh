#!/bin/bash

# Private Fund 项目停止脚本

echo "🛑 正在停止 Private Fund 项目..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 停止所有 pm2 进程
pm2 stop all

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo ""
echo "📝 其他命令："
echo "   完全删除服务: pm2 delete all"
echo "   重新启动: ./start.sh"
echo ""
