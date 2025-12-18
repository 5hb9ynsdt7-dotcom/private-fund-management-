"""
Railway部署数据库迁移脚本
在Railway环境中自动执行所有必要的数据库结构更新
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from app.database import DatabaseConfig
from app.models import Fund
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_fund_short_name(engine):
    """为Fund表添加short_name字段"""
    logger.info("检查fund表的short_name字段...")

    with engine.connect() as conn:
        if check_column_exists(engine, 'fund', 'short_name'):
            logger.info("✓ short_name字段已存在")
            return

        logger.info("添加short_name字段...")
        conn.execute(text("""
            ALTER TABLE fund
            ADD COLUMN short_name VARCHAR(100)
        """))
        conn.commit()
        logger.info("✓ short_name字段添加成功")

        # 为现有数据生成简称
        logger.info("为现有基金生成简称...")
        result = conn.execute(text("SELECT fund_code, fund_name FROM fund"))
        funds = result.fetchall()

        for fund_code, fund_name in funds:
            short_name = Fund.generate_short_name(fund_name)
            conn.execute(
                text("UPDATE fund SET short_name = :short_name WHERE fund_code = :fund_code"),
                {"short_name": short_name, "fund_code": fund_code}
            )

        conn.commit()
        logger.info(f"✓ 为{len(funds)}个基金生成了简称")


def add_dividend_pre_nav(engine):
    """为Dividend表添加pre_dividend_nav字段"""
    logger.info("检查dividend表的pre_dividend_nav字段...")

    with engine.connect() as conn:
        if check_column_exists(engine, 'dividend', 'pre_dividend_nav'):
            logger.info("✓ pre_dividend_nav字段已存在")
            return

        logger.info("添加pre_dividend_nav字段...")
        conn.execute(text("""
            ALTER TABLE dividend
            ADD COLUMN pre_dividend_nav NUMERIC(16, 4)
        """))
        conn.commit()
        logger.info("✓ pre_dividend_nav字段添加成功")


def run_migrations():
    """执行所有迁移"""
    try:
        logger.info("=" * 60)
        logger.info("开始Railway数据库迁移")
        logger.info("=" * 60)

        # 创建数据库引擎
        database_url = DatabaseConfig.get_database_url()
        logger.info(f"数据库URL: {database_url}")
        engine = create_engine(database_url)

        # 执行各项迁移
        add_fund_short_name(engine)
        add_dividend_pre_nav(engine)

        logger.info("=" * 60)
        logger.info("✓ 所有迁移完成")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
