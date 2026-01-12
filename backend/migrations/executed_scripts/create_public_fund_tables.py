"""
公募基金数据库迁移脚本
创建公募基金相关的数据库表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import db_manager
from app.models_public_fund import PublicFund, PublicFundNav, PublicFundAnalysis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_public_fund_tables():
    """创建公募基金相关的数据库表"""
    try:
        logger.info("开始创建公募基金数据表...")

        # 创建所有公募基金相关的表
        PublicFund.__table__.create(bind=db_manager.engine, checkfirst=True)
        logger.info("✓ 创建 public_fund 表成功")

        PublicFundNav.__table__.create(bind=db_manager.engine, checkfirst=True)
        logger.info("✓ 创建 public_fund_nav 表成功")

        PublicFundAnalysis.__table__.create(bind=db_manager.engine, checkfirst=True)
        logger.info("✓ 创建 public_fund_analysis 表成功")

        logger.info("公募基金数据表创建完成！")
        return True

    except Exception as e:
        logger.error(f"创建公募基金数据表失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = create_public_fund_tables()
    if success:
        print("\n✅ 公募基金模块数据库迁移成功！")
        print("已创建以下表：")
        print("  - public_fund (公募基金主数据表)")
        print("  - public_fund_nav (公募基金净值表)")
        print("  - public_fund_analysis (公募基金分析结果表)")
    else:
        print("\n❌ 数据库迁移失败，请检查错误日志")
        sys.exit(1)
