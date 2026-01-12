"""
创建实盘组合相关表
Create portfolio tables
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db_manager
from app.models_portfolio import (
    PublicFundPortfolio,
    PublicFundPortfolioPosition,
    PublicFundPortfolioTransaction,
    PublicFundPortfolioNav
)

def create_portfolio_tables():
    """创建实盘组合相关表"""
    print("开始创建实盘组合相关表...")

    try:
        # 创建表
        PublicFundPortfolio.__table__.create(bind=db_manager.engine, checkfirst=True)
        print("✓ 创建表: public_fund_portfolio")

        PublicFundPortfolioPosition.__table__.create(bind=db_manager.engine, checkfirst=True)
        print("✓ 创建表: public_fund_portfolio_position")

        PublicFundPortfolioTransaction.__table__.create(bind=db_manager.engine, checkfirst=True)
        print("✓ 创建表: public_fund_portfolio_transaction")

        PublicFundPortfolioNav.__table__.create(bind=db_manager.engine, checkfirst=True)
        print("✓ 创建表: public_fund_portfolio_nav")

        print("\n✅ 所有表创建成功！")

    except Exception as e:
        print(f"\n❌ 创建表失败: {str(e)}")
        raise


if __name__ == "__main__":
    create_portfolio_tables()
