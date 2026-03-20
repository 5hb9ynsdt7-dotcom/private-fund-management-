"""
组合净值服务 - 统一管理回测组合和实盘组合的净值数据
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models import PortfolioNav, BacktestPortfolio
from app.models_portfolio import PublicFundPortfolio
import logging

logger = logging.getLogger(__name__)


class PortfolioNavService:
    """组合净值服务"""

    @staticmethod
    def save_portfolio_nav_batch(
        db: Session,
        portfolio_type: str,
        portfolio_id: int,
        portfolio_name: str,
        nav_data: List[Dict]
    ) -> int:
        """
        批量保存组合净值数据

        Args:
            db: 数据库会话
            portfolio_type: 组合类型 (backtest/live)
            portfolio_id: 组合ID
            portfolio_name: 组合名称
            nav_data: 净值数据列表，格式：[
                {
                    'date': date对象或字符串,
                    'unit_nav': float,
                    'accum_nav': float,
                    'daily_return': float (可选),
                    'total_return': float (可选),
                    'total_value': float (可选)
                }
            ]

        Returns:
            保存的记录数
        """
        if not nav_data:
            return 0

        saved_count = 0

        for item in nav_data:
            try:
                # 解析日期
                nav_date = item['date']
                if isinstance(nav_date, str):
                    nav_date = datetime.strptime(nav_date, '%Y-%m-%d').date()
                elif isinstance(nav_date, datetime):
                    nav_date = nav_date.date()

                # 检查是否已存在
                existing = db.query(PortfolioNav).filter(
                    and_(
                        PortfolioNav.portfolio_type == portfolio_type,
                        PortfolioNav.portfolio_id == portfolio_id,
                        PortfolioNav.nav_date == nav_date
                    )
                ).first()

                if existing:
                    # 更新现有记录
                    existing.unit_nav = Decimal(str(item['unit_nav']))
                    existing.accum_nav = Decimal(str(item['accum_nav']))
                    existing.portfolio_name = portfolio_name

                    if 'daily_return' in item and item['daily_return'] is not None:
                        existing.daily_return = Decimal(str(item['daily_return']))
                    if 'total_return' in item and item['total_return'] is not None:
                        existing.total_return = Decimal(str(item['total_return']))
                    if 'total_value' in item and item['total_value'] is not None:
                        existing.total_value = Decimal(str(item['total_value']))

                    existing.updated_at = datetime.now()
                else:
                    # 创建新记录
                    nav_record = PortfolioNav(
                        portfolio_type=portfolio_type,
                        portfolio_id=portfolio_id,
                        portfolio_name=portfolio_name,
                        nav_date=nav_date,
                        unit_nav=Decimal(str(item['unit_nav'])),
                        accum_nav=Decimal(str(item['accum_nav'])),
                        daily_return=Decimal(str(item['daily_return'])) if 'daily_return' in item and item['daily_return'] is not None else None,
                        total_return=Decimal(str(item['total_return'])) if 'total_return' in item and item['total_return'] is not None else None,
                        total_value=Decimal(str(item['total_value'])) if 'total_value' in item and item['total_value'] is not None else None
                    )
                    db.add(nav_record)

                saved_count += 1

            except Exception as e:
                logger.error(f"保存净值数据失败: {item}, 错误: {str(e)}")
                continue

        db.commit()
        logger.info(f"批量保存组合净值: type={portfolio_type}, id={portfolio_id}, count={saved_count}")
        return saved_count

    @staticmethod
    def get_portfolio_nav_history(
        db: Session,
        portfolio_type: str,
        portfolio_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        获取组合净值历史

        Args:
            db: 数据库会话
            portfolio_type: 组合类型
            portfolio_id: 组合ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            净值历史列表
        """
        query = db.query(PortfolioNav).filter(
            and_(
                PortfolioNav.portfolio_type == portfolio_type,
                PortfolioNav.portfolio_id == portfolio_id
            )
        )

        if start_date:
            query = query.filter(PortfolioNav.nav_date >= start_date)
        if end_date:
            query = query.filter(PortfolioNav.nav_date <= end_date)

        nav_records = query.order_by(PortfolioNav.nav_date).all()

        return [
            {
                'date': record.nav_date.strftime('%Y-%m-%d'),
                'unit_nav': float(record.unit_nav),
                'accum_nav': float(record.accum_nav),
                'daily_return': float(record.daily_return) if record.daily_return else None,
                'total_return': float(record.total_return) if record.total_return else None,
                'total_value': float(record.total_value) if record.total_value else None
            }
            for record in nav_records
        ]

    @staticmethod
    def get_latest_nav(
        db: Session,
        portfolio_type: str,
        portfolio_id: int
    ) -> Optional[Dict]:
        """
        获取最新净值

        Args:
            db: 数据库会话
            portfolio_type: 组合类型
            portfolio_id: 组合ID

        Returns:
            最新净值数据或None
        """
        record = db.query(PortfolioNav).filter(
            and_(
                PortfolioNav.portfolio_type == portfolio_type,
                PortfolioNav.portfolio_id == portfolio_id
            )
        ).order_by(desc(PortfolioNav.nav_date)).first()

        if not record:
            return None

        return {
            'date': record.nav_date.strftime('%Y-%m-%d'),
            'unit_nav': float(record.unit_nav),
            'accum_nav': float(record.accum_nav),
            'daily_return': float(record.daily_return) if record.daily_return else None,
            'total_return': float(record.total_return) if record.total_return else None,
            'total_value': float(record.total_value) if record.total_value else None
        }

    @staticmethod
    def delete_portfolio_nav(
        db: Session,
        portfolio_type: str,
        portfolio_id: int
    ) -> int:
        """
        删除组合的所有净值数据

        Args:
            db: 数据库会话
            portfolio_type: 组合类型
            portfolio_id: 组合ID

        Returns:
            删除的记录数
        """
        count = db.query(PortfolioNav).filter(
            and_(
                PortfolioNav.portfolio_type == portfolio_type,
                PortfolioNav.portfolio_id == portfolio_id
            )
        ).delete()

        db.commit()
        logger.info(f"删除组合净值: type={portfolio_type}, id={portfolio_id}, count={count}")
        return count

    @staticmethod
    def extract_weekly_nav(nav_curve: List[Dict]) -> List[Dict]:
        """
        从日度净值曲线中提取周度净值（每周五或最后交易日）

        Args:
            nav_curve: 日度净值曲线，格式：[
                {'date': 'YYYY-MM-DD', 'unit_nav': float, 'accum_nav': float, ...}
            ]

        Returns:
            周度净值列表
        """
        if not nav_curve:
            return []

        weekly_navs = []
        current_week = None
        week_last_nav = None

        for item in nav_curve:
            nav_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
            # 获取周数（ISO周）
            week_num = nav_date.isocalendar()[1]
            year = nav_date.year

            week_key = f"{year}-W{week_num}"

            if current_week != week_key:
                # 新的一周，保存上周最后一天的净值
                if week_last_nav:
                    weekly_navs.append(week_last_nav)
                current_week = week_key

            # 更新本周最后一天的净值
            week_last_nav = item

        # 添加最后一周的净值
        if week_last_nav:
            weekly_navs.append(week_last_nav)

        return weekly_navs

    @staticmethod
    def get_portfolio_info(
        db: Session,
        portfolio_type: str,
        portfolio_id: int
    ) -> Optional[Dict]:
        """
        获取组合基本信息

        Args:
            db: 数据库会话
            portfolio_type: 组合类型
            portfolio_id: 组合ID

        Returns:
            组合信息或None
        """
        if portfolio_type == 'backtest':
            portfolio = db.query(BacktestPortfolio).filter(
                BacktestPortfolio.id == portfolio_id
            ).first()
            if portfolio:
                return {
                    'id': portfolio.id,
                    'name': portfolio.portfolio_name,
                    'type': 'backtest'
                }
        elif portfolio_type == 'live':
            portfolio = db.query(PublicFundPortfolio).filter(
                PublicFundPortfolio.id == portfolio_id
            ).first()
            if portfolio:
                return {
                    'id': portfolio.id,
                    'name': portfolio.portfolio_name,
                    'type': 'live'
                }

        return None
