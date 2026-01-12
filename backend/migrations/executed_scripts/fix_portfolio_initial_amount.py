"""
修复实盘组合的 initial_amount 字段
将 initial_amount 重置为所有买入交易金额的累加和
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库连接
DATABASE_URL = "sqlite:///./privatefund_dev.db"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def fix_initial_amounts():
    """修复所有组合的 initial_amount"""
    db = SessionLocal()

    try:
        # 获取所有组合
        portfolios = db.execute(
            text("SELECT id, portfolio_name FROM public_fund_portfolio")
        ).fetchall()

        logger.info(f"找到 {len(portfolios)} 个组合需要修复")

        for portfolio in portfolios:
            portfolio_id = portfolio[0]
            portfolio_name = portfolio[1]

            # 计算该组合所有买入交易的总金额
            result = db.execute(
                text("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM public_fund_portfolio_transaction
                    WHERE portfolio_id = :portfolio_id
                    AND transaction_type = 'buy'
                """),
                {"portfolio_id": portfolio_id}
            ).fetchone()

            total_invested = result[0] if result else 0

            # 更新 initial_amount
            db.execute(
                text("""
                    UPDATE public_fund_portfolio
                    SET initial_amount = :total_invested
                    WHERE id = :portfolio_id
                """),
                {
                    "portfolio_id": portfolio_id,
                    "total_invested": total_invested
                }
            )

            logger.info(f"组合 [{portfolio_name}] (ID: {portfolio_id}): "
                       f"initial_amount 已更新为 {total_invested}")

        db.commit()
        logger.info("✓ 所有组合的 initial_amount 修复完成")

    except Exception as e:
        db.rollback()
        logger.error(f"修复失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始修复实盘组合 initial_amount 数据")
    logger.info("=" * 60)

    fix_initial_amounts()

    logger.info("=" * 60)
    logger.info("修复完成")
    logger.info("=" * 60)
