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


def add_fund_timestamps(engine):
    """为Fund表添加created_at和updated_at时间戳字段"""
    logger.info("检查 fund.created_at 和 fund.updated_at 字段...")

    try:
        with engine.connect() as conn:
            # 检查created_at字段
            if not check_column_exists(engine, 'fund', 'created_at'):
                logger.info("添加 fund.created_at 字段...")
                # SQLite不支持带CURRENT_TIMESTAMP的ALTER TABLE ADD COLUMN，先添加为NULL
                conn.execute(text("""
                    ALTER TABLE fund
                    ADD COLUMN created_at TIMESTAMP
                """))
                conn.commit()

                # 为现有记录设置当前时间戳
                conn.execute(text("""
                    UPDATE fund
                    SET created_at = CURRENT_TIMESTAMP
                    WHERE created_at IS NULL
                """))
                conn.commit()
                logger.info("✓ fund.created_at 字段添加成功")
            else:
                logger.info("✓ fund.created_at 字段已存在")

            # 检查updated_at字段
            if not check_column_exists(engine, 'fund', 'updated_at'):
                logger.info("添加 fund.updated_at 字段...")
                # SQLite不支持带CURRENT_TIMESTAMP的ALTER TABLE ADD COLUMN，先添加为NULL
                conn.execute(text("""
                    ALTER TABLE fund
                    ADD COLUMN updated_at TIMESTAMP
                """))
                conn.commit()

                # 为现有记录设置当前时间戳
                conn.execute(text("""
                    UPDATE fund
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE updated_at IS NULL
                """))
                conn.commit()
                logger.info("✓ fund.updated_at 字段添加成功")
            else:
                logger.info("✓ fund.updated_at 字段已存在")

    except Exception as e:
        logger.error(f"添加Fund时间戳字段失败: {e}")
        raise


def create_weekly_excess_cache_table(engine):
    """创建周度超额缓存表"""
    logger.info("检查 weekly_excess_cache 表...")

    try:
        inspector = inspect(engine)
        if 'weekly_excess_cache' in inspector.get_table_names():
            logger.info("✓ weekly_excess_cache 表已存在")
            return

        with engine.connect() as conn:
            logger.info("创建 weekly_excess_cache 表...")
            conn.execute(text("""
                CREATE TABLE weekly_excess_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fund_code VARCHAR(20) NOT NULL,
                    tracking_index VARCHAR(20) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    excess_data TEXT NOT NULL,
                    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(fund_code, tracking_index, start_date, end_date)
                )
            """))

            # 创建索引
            conn.execute(text("""
                CREATE INDEX idx_weekly_excess_fund
                ON weekly_excess_cache(fund_code)
            """))

            conn.execute(text("""
                CREATE INDEX idx_weekly_excess_date
                ON weekly_excess_cache(updated_at)
            """))

            conn.commit()
            logger.info("✓ weekly_excess_cache 表创建成功")

    except Exception as e:
        logger.error(f"创建 weekly_excess_cache 表失败: {e}")
        raise


def add_fund_schedule_fee_structure(engine):
    """为FundScheduleRule表添加fee_structure字段"""
    logger.info("检查 fund_schedule_rule.fee_structure 字段...")

    try:
        with engine.connect() as conn:
            if check_column_exists(engine, 'fund_schedule_rule', 'fee_structure'):
                logger.info("✓ fund_schedule_rule.fee_structure 字段已存在")
                return

            logger.info("添加 fund_schedule_rule.fee_structure 字段...")
            conn.execute(text("""
                ALTER TABLE fund_schedule_rule
                ADD COLUMN fee_structure TEXT
            """))
            conn.commit()
            logger.info("✓ fund_schedule_rule.fee_structure 字段添加成功")
    except Exception as e:
        logger.error(f"添加 fund_schedule_rule.fee_structure 字段失败: {e}")
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
        add_fund_timestamps(engine)  # 新增：添加时间戳字段
        create_weekly_excess_cache_table(engine)  # 新增：创建周度超额缓存表
        add_fund_schedule_fee_structure(engine)  # 新增：添加费用结构字段

        logger.info("=" * 60)
        logger.info("✓ 所有数据库迁移完成")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"✗ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
