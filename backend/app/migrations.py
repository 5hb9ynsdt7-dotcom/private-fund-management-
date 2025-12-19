"""
数据库迁移模块
自动在应用启动时执行数据库 schema 更新
"""

from sqlalchemy import create_engine, text, inspect
from .database import DatabaseConfig
from .models import Fund
import logging

logger = logging.getLogger(__name__)


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """检查表中是否存在指定列"""
    inspector = inspect(engine)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        logger.error(f"检查列 {table_name}.{column_name} 失败: {e}")
        return False


def add_fund_short_name(engine):
    """为Fund表添加short_name字段"""
    logger.info("检查 fund.short_name 字段...")

    try:
        with engine.connect() as conn:
            if check_column_exists(engine, 'fund', 'short_name'):
                logger.info("✓ fund.short_name 字段已存在")
                return

            logger.info("添加 fund.short_name 字段...")
            conn.execute(text("""
                ALTER TABLE fund
                ADD COLUMN short_name VARCHAR(100)
            """))
            conn.commit()
            logger.info("✓ fund.short_name 字段添加成功")

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
            logger.info(f"✓ 为 {len(funds)} 个基金生成了简称")
    except Exception as e:
        logger.error(f"添加 fund.short_name 字段失败: {e}")
        raise


def add_dividend_pre_nav(engine):
    """为Dividend表添加pre_dividend_nav字段"""
    logger.info("检查 dividend.pre_dividend_nav 字段...")

    try:
        with engine.connect() as conn:
            if check_column_exists(engine, 'dividend', 'pre_dividend_nav'):
                logger.info("✓ dividend.pre_dividend_nav 字段已存在")
                return

            logger.info("添加 dividend.pre_dividend_nav 字段...")
            conn.execute(text("""
                ALTER TABLE dividend
                ADD COLUMN pre_dividend_nav NUMERIC(16, 4)
            """))
            conn.commit()
            logger.info("✓ dividend.pre_dividend_nav 字段添加成功")
    except Exception as e:
        logger.error(f"添加 dividend.pre_dividend_nav 字段失败: {e}")
        raise


def run_migrations():
    """
    执行所有数据库迁移
    在应用启动时自动调用
    """
    try:
        logger.info("=" * 60)
        logger.info("开始执行数据库迁移")
        logger.info("=" * 60)

        # 创建数据库引擎
        database_url = DatabaseConfig.get_database_url()
        engine = create_engine(database_url)

        # 执行各项迁移
        add_fund_short_name(engine)
        add_dividend_pre_nav(engine)

        logger.info("=" * 60)
        logger.info("✓ 所有数据库迁移完成")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"✗ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
