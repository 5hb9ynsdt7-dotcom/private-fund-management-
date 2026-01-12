#!/bin/bash
# 项目清理脚本 - Private Fund Management System
# 创建日期: 2025-01-12
# 用途: 清理冗余文件、缓存和临时文件

echo "🧹 开始清理项目..."
echo ""

# 1. 删除空数据库文件
echo "📁 清理空数据库文件..."
if [ -f "backend/app.db" ]; then
    rm backend/app.db
    echo "  ✓ 删除 backend/app.db"
fi

if [ -f "backend/app/trading.db" ]; then
    rm backend/app/trading.db
    echo "  ✓ 删除 backend/app/trading.db"
fi

# 2. 删除系统缓存文件
echo ""
echo "🗑️  清理系统缓存文件..."
if [ -f ".DS_Store" ]; then
    rm .DS_Store
    echo "  ✓ 删除 .DS_Store"
fi

# 3. 归档迁移脚本
echo ""
echo "📦 归档迁移脚本..."
mkdir -p backend/migrations/executed_scripts

scripts=(
    "backend/create_portfolio_tables.py"
    "backend/create_project_holding_tables.py"
    "backend/create_public_fund_tables.py"
    "backend/fix_portfolio_initial_amount.py"
    "backend/migrate_all_dbs.py"
    "backend/update_fund_name.py"
    "backend/add_pre_dividend_nav_column.py"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" backend/migrations/executed_scripts/
        echo "  ✓ 归档 $(basename $script)"
    fi
done

# 4. 删除前端冗余文件
echo ""
echo "🎨 清理前端冗余文件..."
if [ -f "frontend/src/views/PublicFund.vue" ]; then
    rm frontend/src/views/PublicFund.vue
    echo "  ✓ 删除 frontend/src/views/PublicFund.vue"
fi

# 5. 清理构建产物（可选）
echo ""
read -p "是否清理前端构建产物 frontend/dist/? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "frontend/dist" ]; then
        rm -rf frontend/dist/
        echo "  ✓ 删除 frontend/dist/"
    fi
fi

echo ""
echo "✅ 清理完成！"
echo ""
echo "📊 清理统计："
echo "  - 删除空数据库文件: 2个"
echo "  - 删除系统缓存: 1个"
echo "  - 归档迁移脚本: 7个"
echo "  - 删除冗余页面: 1个"
echo ""
echo "💡 提示："
echo "  - 迁移脚本已移至 backend/migrations/executed_scripts/"
echo "  - 如需恢复，可从该目录找回"
echo "  - 建议运行 'git status' 检查变更"
