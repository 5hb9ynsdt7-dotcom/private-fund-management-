"""
计算并更新所有基金的复权累计净值
一次性脚本，用于填充 nav.adjusted_accum_nav 字段
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import DatabaseConfig
from app.models import Nav, Dividend
from sqlalchemy import and_
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_adjusted_nav_for_fund(session, fund_code):
    """计算单个基金的所有复权累计净值"""
    try:
        # 获取该基金的所有净值记录（按日期升序）
        nav_records = session.query(Nav).filter(
            Nav.fund_code == fund_code
        ).order_by(Nav.nav_date).all()

        if not nav_records:
            logger.warning(f"基金 {fund_code} 没有净值数据")
            return 0

        # 获取该基金的所有分红记录
        dividends = session.query(Dividend).filter(
            Dividend.fund_code == fund_code
        ).order_by(Dividend.ex_dividend_date).all()

        # 创建分红字典
        dividend_dict = {}
        for div in dividends:
            if div.ex_dividend_date and div.dividend_per_share:
                date_str = div.ex_dividend_date.strftime('%Y-%m-%d')
                dividend_dict[date_str] = {
                    'dividend_amount': float(div.dividend_per_share),
                    'pre_dividend_nav': float(div.pre_dividend_nav) if div.pre_dividend_nav else None
                }

        # 计算复权累计净值
        prev_adjusted_nav = None
        prev_unit_nav = None
        updated_count = 0

        for i, nav in enumerate(nav_records):
            date_str = nav.nav_date.strftime('%Y-%m-%d')
            current_unit_nav = float(nav.unit_nav)

            if i == 0:
                # 第一个净值日：复权累计净值 = 单位净值
                adjusted_accum_nav = current_unit_nav
            else:
                # 后续净值日：使用复利链条法计算
                # 检查当前日期是否有分红
                dividend_amount = 0.0
                if date_str in dividend_dict:
                    dividend_amount = dividend_dict[date_str]['dividend_amount']

                # 计算复权累计净值
                # F_t = F_{t-1} × (NV_t + D_t) / NV_{t-1}
                if prev_unit_nav > 0:
                    adjusted_accum_nav = prev_adjusted_nav * (current_unit_nav + dividend_amount) / prev_unit_nav
                else:
                    adjusted_accum_nav = current_unit_nav

            # 更新数据库
            nav.adjusted_accum_nav = Decimal(str(round(adjusted_accum_nav, 4)))
            updated_count += 1

            # 更新前一日的值
            prev_adjusted_nav = adjusted_accum_nav
            prev_unit_nav = current_unit_nav

        session.commit()
        return updated_count

    except Exception as e:
        logger.error(f"计算基金 {fund_code} 复权净值失败: {e}")
        session.rollback()
        return 0


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始计算所有基金的复权累计净值")
    logger.info("=" * 60)

    # 创建数据库连接
    database_url = DatabaseConfig.get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 获取所有基金代码
        fund_codes = session.query(Nav.fund_code).distinct().all()
        fund_codes = [code[0] for code in fund_codes]

        logger.info(f"共找到 {len(fund_codes)} 个基金")

        total_updated = 0
        for i, fund_code in enumerate(fund_codes, 1):
            logger.info(f"[{i}/{len(fund_codes)}] 处理基金 {fund_code}...")
            updated = calculate_adjusted_nav_for_fund(session, fund_code)
            total_updated += updated
            logger.info(f"  ✓ 更新了 {updated} 条净值记录")

        logger.info("=" * 60)
        logger.info(f"✓ 完成！共更新 {total_updated} 条净值记录")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
