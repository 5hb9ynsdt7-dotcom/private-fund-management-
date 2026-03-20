"""
公募基金实盘组合服务
Public Fund Portfolio Service
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import logging

from ..models_portfolio import (
    PublicFundPortfolio,
    PublicFundPortfolioPosition,
    PublicFundPortfolioTransaction,
    PublicFundPortfolioNav
)
from ..models_public_fund import PublicFund, PublicFundNav
from ..models import Nav, Fund  # 添加私募基金模型
from ..schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    TransactionCreate
)

logger = logging.getLogger(__name__)


class PortfolioService:
    """实盘组合服务"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 辅助方法 ==========

    def _get_fund_nav(self, fund_code: str, nav_date: date, portfolio_type: str):
        """
        根据组合类型从不同的表获取净值

        Args:
            fund_code: 基金代码
            nav_date: 净值日期
            portfolio_type: 组合类型 ('public' 或 'private')

        Returns:
            包含 unit_nav, accum_nav, nav_date 的字典，未找到则返回 None
        """
        if portfolio_type == 'private':
            # 私募基金：从 nav 表获取
            nav = self.db.query(Nav).filter(
                and_(
                    Nav.fund_code == fund_code,
                    Nav.nav_date <= nav_date
                )
            ).order_by(desc(Nav.nav_date)).first()

            if nav:
                return {
                    'unit_nav': nav.unit_nav,
                    'accum_nav': nav.accum_nav,
                    'nav_date': nav.nav_date
                }
        else:
            # 公募基金：从 public_fund_nav 表获取
            nav = self.db.query(PublicFundNav).filter(
                and_(
                    PublicFundNav.fund_code == fund_code,
                    PublicFundNav.nav_date <= nav_date
                )
            ).order_by(desc(PublicFundNav.nav_date)).first()

            if nav:
                return {
                    'unit_nav': nav.unit_nav,
                    'accum_nav': nav.accum_nav,
                    'nav_date': nav.nav_date
                }

        return None

    def _get_latest_nav(self, fund_code: str, portfolio_type: str, as_of_date: Optional[date] = None):
        """
        获取最新净值（在指定日期或之前）

        Args:
            fund_code: 基金代码
            portfolio_type: 组合类型 ('public' 或 'private')
            as_of_date: 截止日期，默认为今天

        Returns:
            包含 unit_nav, accum_nav, nav_date 的字典，未找到则返回 None
        """
        if not as_of_date:
            as_of_date = date.today()

        if portfolio_type == 'private':
            # 私募基金：从 nav 表获取
            nav = self.db.query(Nav).filter(
                and_(
                    Nav.fund_code == fund_code,
                    Nav.nav_date <= as_of_date
                )
            ).order_by(desc(Nav.nav_date)).first()
        else:
            # 公募基金：从 public_fund_nav 表获取
            nav = self.db.query(PublicFundNav).filter(
                and_(
                    PublicFundNav.fund_code == fund_code,
                    PublicFundNav.nav_date <= as_of_date
                )
            ).order_by(desc(PublicFundNav.nav_date)).first()

        if nav:
            return {
                'unit_nav': nav.unit_nav,
                'accum_nav': nav.accum_nav,
                'nav_date': nav.nav_date
            }

        return None

    def _verify_fund_exists(self, fund_code: str, portfolio_type: str):
        """
        验证基金是否存在

        Args:
            fund_code: 基金代码
            portfolio_type: 组合类型 ('public' 或 'private')

        Returns:
            基金记录，不存在则返回 None
        """
        if portfolio_type == 'private':
            # 私募基金：从 fund 表查询
            return self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
        else:
            # 公募基金：从 public_fund 表查询
            return self.db.query(PublicFund).filter(PublicFund.fund_code == fund_code).first()

    # ========== 组合管理 ==========

    def create_portfolio(self, portfolio_data: PortfolioCreate) -> PublicFundPortfolio:
        """
        创建新组合（initial_amount 由买入交易自动累加）
        """
        try:
            portfolio = PublicFundPortfolio(
                portfolio_name=portfolio_data.portfolio_name,
                description=portfolio_data.description,
                portfolio_type=portfolio_data.portfolio_type or 'public',
                update_frequency=portfolio_data.update_frequency or 'daily',
                initial_amount=Decimal('0'),  # 初始为0，由交易累加
                cash_balance=Decimal('0')     # 不使用，保留字段兼容
            )

            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)

            logger.info(f"创建组合成功: {portfolio.portfolio_name} (类型: {portfolio.portfolio_type})")
            return portfolio

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建组合失败: {str(e)}")
            raise

    def get_portfolio_list(self, is_active: Optional[bool] = None) -> List[PublicFundPortfolio]:
        """
        获取组合列表
        """
        try:
            query = self.db.query(PublicFundPortfolio)

            if is_active is not None:
                query = query.filter(PublicFundPortfolio.is_active == is_active)

            portfolios = query.order_by(desc(PublicFundPortfolio.updated_at)).all()
            return portfolios

        except Exception as e:
            logger.error(f"获取组合列表失败: {str(e)}")
            raise

    def get_portfolio(self, portfolio_id: int) -> Optional[PublicFundPortfolio]:
        """
        获取单个组合
        """
        return self.db.query(PublicFundPortfolio).filter(
            PublicFundPortfolio.id == portfolio_id
        ).first()

    def update_portfolio(self, portfolio_id: int, update_data: PortfolioUpdate) -> PublicFundPortfolio:
        """
        更新组合信息
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"组合 {portfolio_id} 不存在")

            # 更新字段
            if update_data.portfolio_name is not None:
                portfolio.portfolio_name = update_data.portfolio_name
            if update_data.description is not None:
                portfolio.description = update_data.description
            if update_data.cash_balance is not None:
                portfolio.cash_balance = update_data.cash_balance
            if update_data.is_active is not None:
                portfolio.is_active = update_data.is_active

            self.db.commit()
            self.db.refresh(portfolio)

            logger.info(f"更新组合成功: {portfolio_id}")
            return portfolio

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新组合失败: {str(e)}")
            raise

    def delete_portfolio(self, portfolio_id: int):
        """
        删除组合（级联删除所有相关数据）
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"组合 {portfolio_id} 不存在")

            self.db.delete(portfolio)
            self.db.commit()

            logger.info(f"删除组合成功: {portfolio_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除组合失败: {str(e)}")
            raise

    # ========== 交易记录 ==========

    def add_transaction(self, portfolio_id: int, transaction_data: TransactionCreate) -> PublicFundPortfolioTransaction:
        """
        添加交易记录并更新持仓
        支持四种交易类型：
        - buy: 买入（需要金额，自动计算份额）
        - sell: 卖出（需要金额或份额）
        - cash_dividend: 现金分红（需要金额，增加盈亏）
        - reinvest_dividend: 红利再投（需要份额，增加持仓）
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"组合 {portfolio_id} 不存在")

            # 验证基金是否存在（根据组合类型查询不同的表）
            fund = self._verify_fund_exists(transaction_data.fund_code, portfolio.portfolio_type)
            if not fund:
                fund_type_name = "私募基金" if portfolio.portfolio_type == 'private' else "公募基金"
                raise ValueError(f"基金 {transaction_data.fund_code} 不存在，请先在{fund_type_name}库中添加该基金")

            # 根据交易类型验证必填字段
            if transaction_data.transaction_type in ['buy', 'sell', 'cash_dividend']:
                if not transaction_data.amount or transaction_data.amount == 0:
                    raise ValueError(f"{transaction_data.transaction_type} 交易必须提供金额")

            if transaction_data.transaction_type == 'reinvest_dividend':
                if not transaction_data.shares or transaction_data.shares == 0:
                    raise ValueError("红利再投交易必须提供份额")

            # 自动获取交易日期的净值（如果未提供）- 使用新的辅助方法
            nav_value = transaction_data.nav
            if not nav_value:
                nav_data = self._get_fund_nav(
                    transaction_data.fund_code,
                    transaction_data.transaction_date,
                    portfolio.portfolio_type
                )

                if not nav_data:
                    fund_type_name = "私募基金" if portfolio.portfolio_type == 'private' else "公募基金"
                    raise ValueError(
                        f"未找到{fund_type_name} {transaction_data.fund_code} 在 {transaction_data.transaction_date} 或之前的净值数据，请先添加净值"
                    )

                nav_value = nav_data['unit_nav']
                logger.info(f"自动获取净值: {transaction_data.fund_code} 日期:{nav_data['nav_date']} 净值:{nav_value}")

            # 计算份额和金额
            shares = transaction_data.shares
            amount = transaction_data.amount

            if transaction_data.transaction_type in ['buy', 'sell']:
                # 买入/卖出：自动计算份额（如果未提供）
                if not shares or shares == 0:
                    if not amount or amount == 0:
                        raise ValueError("请提供交易金额或交易份额")
                    shares = amount / nav_value
                    logger.info(f"自动计算份额: 金额:{amount} / 净值:{nav_value} = {shares}")
                elif not amount or amount == 0:
                    # 如果只提供了份额，计算金额
                    amount = shares * nav_value
                    logger.info(f"自动计算金额: 份额:{shares} * 净值:{nav_value} = {amount}")

            elif transaction_data.transaction_type == 'cash_dividend':
                # 现金分红：金额已提供，份额设为0
                shares = Decimal('0')

            elif transaction_data.transaction_type == 'reinvest_dividend':
                # 红利再投：份额已提供，金额设为0
                amount = Decimal('0')

            # 创建交易记录
            transaction = PublicFundPortfolioTransaction(
                portfolio_id=portfolio_id,
                fund_code=transaction_data.fund_code,
                transaction_type=transaction_data.transaction_type,
                transaction_date=transaction_data.transaction_date,
                amount=amount,
                shares=shares,
                nav=nav_value,
                fee=transaction_data.fee or Decimal('0'),
                note=transaction_data.note
            )

            self.db.add(transaction)

            # 更新持仓（使用计算后的数据）
            updated_transaction_data = TransactionCreate(
                fund_code=transaction_data.fund_code,
                transaction_type=transaction_data.transaction_type,
                transaction_date=transaction_data.transaction_date,
                amount=amount,
                shares=shares,
                nav=nav_value,
                fee=transaction_data.fee,
                note=transaction_data.note
            )
            self._update_position(portfolio_id, updated_transaction_data)

            # 更新总投入金额
            if transaction_data.transaction_type == 'buy':
                # 买入：增加总投入
                portfolio.initial_amount += amount
            elif transaction_data.transaction_type == 'cash_dividend':
                # 现金分红：减少总投入（相当于收回部分投资）
                portfolio.initial_amount -= amount
            # 卖出和红利再投不改变总投入

            self.db.commit()
            self.db.refresh(transaction)

            logger.info(f"添加交易记录成功: {transaction_data.transaction_type} {transaction_data.fund_code}")
            return transaction

        except Exception as e:
            self.db.rollback()
            logger.error(f"添加交易记录失败: {str(e)}")
            raise

    def _update_position(self, portfolio_id: int, transaction: TransactionCreate):
        """
        根据交易记录更新持仓
        """
        # 查找或创建持仓记录
        position = self.db.query(PublicFundPortfolioPosition).filter(
            and_(
                PublicFundPortfolioPosition.portfolio_id == portfolio_id,
                PublicFundPortfolioPosition.fund_code == transaction.fund_code
            )
        ).first()

        if not position:
            # 新建持仓
            position = PublicFundPortfolioPosition(
                portfolio_id=portfolio_id,
                fund_code=transaction.fund_code,
                shares=Decimal('0'),
                cost_amount=Decimal('0')
            )
            self.db.add(position)

        if transaction.transaction_type == 'buy':
            # 买入：增加份额和成本
            position.shares += transaction.shares
            position.cost_amount += transaction.amount
            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares

        elif transaction.transaction_type == 'sell':
            # 卖出：减少份额和成本
            if position.shares < transaction.shares:
                raise ValueError(f"持仓份额不足，当前持仓: {position.shares}，卖出: {transaction.shares}")

            # 按比例减少成本
            cost_ratio = transaction.shares / position.shares
            position.shares -= transaction.shares
            position.cost_amount -= position.cost_amount * cost_ratio

            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares
            else:
                position.avg_cost_nav = None

        elif transaction.transaction_type == 'cash_dividend':
            # 现金分红：不改变份额，减少成本（相当于收回部分投资）
            position.cost_amount -= transaction.amount
            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares

        elif transaction.transaction_type == 'reinvest_dividend':
            # 红利再投：增加份额，不改变成本（分红转为份额）
            position.shares += transaction.shares
            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares

    def get_transactions(self, portfolio_id: int, limit: int = 100) -> List[PublicFundPortfolioTransaction]:
        """
        获取交易记录
        """
        try:
            transactions = self.db.query(PublicFundPortfolioTransaction)\
                .filter(PublicFundPortfolioTransaction.portfolio_id == portfolio_id)\
                .order_by(desc(PublicFundPortfolioTransaction.transaction_date))\
                .limit(limit)\
                .all()

            return transactions

        except Exception as e:
            logger.error(f"获取交易记录失败: {str(e)}")
            raise

    def delete_transaction(self, portfolio_id: int, transaction_id: int):
        """
        删除交易记录并回滚持仓和现金余额
        """
        try:
            # 获取交易记录
            transaction = self.db.query(PublicFundPortfolioTransaction).filter(
                and_(
                    PublicFundPortfolioTransaction.id == transaction_id,
                    PublicFundPortfolioTransaction.portfolio_id == portfolio_id
                )
            ).first()

            if not transaction:
                raise ValueError(f"交易记录 {transaction_id} 不存在")

            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"组合 {portfolio_id} 不存在")

            # 回滚持仓
            self._rollback_position(portfolio_id, transaction)

            # 回滚总投入
            if transaction.transaction_type == 'buy':
                # 回滚买入：减少总投入
                portfolio.initial_amount -= transaction.amount
            elif transaction.transaction_type == 'cash_dividend':
                # 回滚现金分红：增加总投入
                portfolio.initial_amount += transaction.amount
            # 卖出和红利再投不改变总投入

            # 删除交易记录
            self.db.delete(transaction)
            self.db.commit()

            logger.info(f"删除交易记录成功: {transaction_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除交易记录失败: {str(e)}")
            raise

    def _rollback_position(self, portfolio_id: int, transaction: PublicFundPortfolioTransaction):
        """
        根据交易记录回滚持仓
        """
        # 查找持仓记录
        position = self.db.query(PublicFundPortfolioPosition).filter(
            and_(
                PublicFundPortfolioPosition.portfolio_id == portfolio_id,
                PublicFundPortfolioPosition.fund_code == transaction.fund_code
            )
        ).first()

        if not position:
            raise ValueError(f"未找到对应的持仓记录")

        if transaction.transaction_type == 'buy':
            # 回滚买入：减少份额和成本
            position.shares -= transaction.shares
            position.cost_amount -= transaction.amount

            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares
            else:
                position.avg_cost_nav = None

        elif transaction.transaction_type == 'sell':
            # 回滚卖出：增加份额和成本
            # 计算原来的成本比例
            if position.shares > 0:
                avg_cost = position.cost_amount / position.shares
            else:
                # 如果当前份额为0，使用交易净值作为成本
                avg_cost = transaction.nav if transaction.nav else Decimal('0')

            position.shares += transaction.shares
            position.cost_amount += (transaction.shares * avg_cost)

            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares

        elif transaction.transaction_type == 'cash_dividend':
            # 回滚现金分红：增加成本
            position.cost_amount += transaction.amount
            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares

        elif transaction.transaction_type == 'reinvest_dividend':
            # 回滚红利再投：减少份额
            position.shares -= transaction.shares
            # 更新平均成本净值
            if position.shares > 0:
                position.avg_cost_nav = position.cost_amount / position.shares
            else:
                position.avg_cost_nav = None

    # ========== 持仓查询 ==========

    def get_positions(self, portfolio_id: int) -> List[PublicFundPortfolioPosition]:
        """
        获取当前持仓
        """
        try:
            positions = self.db.query(PublicFundPortfolioPosition)\
                .filter(
                    and_(
                        PublicFundPortfolioPosition.portfolio_id == portfolio_id,
                        PublicFundPortfolioPosition.shares > 0  # 只返回有份额的持仓
                    )
                )\
                .all()

            return positions

        except Exception as e:
            logger.error(f"获取持仓失败: {str(e)}")
            raise

    # ========== 组合净值计算 ==========

    def calculate_portfolio_value(self, portfolio_id: int, as_of_date: Optional[date] = None) -> dict:
        """
        计算组合当前市值和收益
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"组合 {portfolio_id} 不存在")

            if not as_of_date:
                as_of_date = date.today()

            positions = self.get_positions(portfolio_id)

            total_market_value = Decimal('0')
            position_details = []

            for position in positions:
                # 获取最新净值 - 使用新的辅助方法
                nav_data = self._get_latest_nav(
                    position.fund_code,
                    portfolio.portfolio_type,
                    as_of_date
                )

                if nav_data:
                    current_nav = nav_data['unit_nav']
                    current_value = position.shares * current_nav
                    total_market_value += current_value

                    profit_loss = current_value - position.cost_amount
                    profit_loss_rate = (profit_loss / position.cost_amount * 100) if position.cost_amount > 0 else Decimal('0')

                    position_details.append({
                        'fund_code': position.fund_code,
                        'shares': position.shares,
                        'cost_amount': position.cost_amount,
                        'avg_cost_nav': position.avg_cost_nav,
                        'current_nav': current_nav,
                        'current_nav_date': nav_data['nav_date'],
                        'current_value': current_value,
                        'profit_loss': profit_loss,
                        'profit_loss_rate': profit_loss_rate
                    })

            # 累计收益 = 持仓市值 - 累计投入
            total_return = total_market_value - portfolio.initial_amount

            # 累计收益率
            total_return_rate = (total_return / portfolio.initial_amount * 100) if portfolio.initial_amount > 0 else Decimal('0')

            return {
                'portfolio_id': portfolio_id,
                'as_of_date': as_of_date,
                'initial_amount': portfolio.initial_amount,  # 累计投入
                'total_market_value': total_market_value,  # 当前市值（持仓）
                'total_return': total_return,  # 累计收益
                'total_return_rate': total_return_rate,  # 收益率
                'positions': position_details
            }

        except Exception as e:
            logger.error(f"计算组合市值失败: {str(e)}")
            raise

    def save_portfolio_nav(self, portfolio_id: int, nav_date: Optional[date] = None):
        """
        保存组合每日净值快照
        """
        try:
            if not nav_date:
                nav_date = date.today()

            # 计算当前组合价值
            value_data = self.calculate_portfolio_value(portfolio_id, nav_date)

            # 检查是否已存在该日期的净值记录
            existing_nav = self.db.query(PublicFundPortfolioNav).filter(
                and_(
                    PublicFundPortfolioNav.portfolio_id == portfolio_id,
                    PublicFundPortfolioNav.nav_date == nav_date
                )
            ).first()

            if existing_nav:
                # 更新现有记录
                existing_nav.total_market_value = value_data['total_market_value']
                existing_nav.cash_balance = Decimal('0')  # 不使用
                existing_nav.total_assets = value_data['total_market_value']  # 总资产=持仓市值
                existing_nav.cumulative_return = value_data['total_return']
                existing_nav.cumulative_return_rate = value_data['total_return_rate']
            else:
                # 创建新记录
                nav_record = PublicFundPortfolioNav(
                    portfolio_id=portfolio_id,
                    nav_date=nav_date,
                    total_market_value=value_data['total_market_value'],
                    cash_balance=Decimal('0'),  # 不使用
                    total_assets=value_data['total_market_value'],  # 总资产=持仓市值
                    cumulative_return=value_data['total_return'],
                    cumulative_return_rate=value_data['total_return_rate']
                )
                self.db.add(nav_record)

            self.db.commit()
            logger.info(f"保存组合净值成功: {portfolio_id}, {nav_date}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存组合净值失败: {str(e)}")
            raise

    def get_nav_history(self, portfolio_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[PublicFundPortfolioNav]:
        """
        获取组合净值历史
        """
        try:
            query = self.db.query(PublicFundPortfolioNav)\
                .filter(PublicFundPortfolioNav.portfolio_id == portfolio_id)

            if start_date:
                query = query.filter(PublicFundPortfolioNav.nav_date >= start_date)
            if end_date:
                query = query.filter(PublicFundPortfolioNav.nav_date <= end_date)

            nav_history = query.order_by(PublicFundPortfolioNav.nav_date).all()
            return nav_history

        except Exception as e:
            logger.error(f"获取净值历史失败: {str(e)}")
            raise

    def calculate_and_save_weekly_nav(self, portfolio_id: int) -> int:
        """
        计算实盘组合的周度净值并保存到统一的 PortfolioNav 表
        用于业绩PK对比

        Args:
            portfolio_id: 组合ID

        Returns:
            保存的周度净值记录数
        """
        try:
            from .portfolio_nav_service import PortfolioNavService
            import pandas as pd

            # 获取组合信息
            portfolio = self.db.query(PublicFundPortfolio).filter(
                PublicFundPortfolio.id == portfolio_id
            ).first()

            if not portfolio:
                raise ValueError(f"组合不存在: {portfolio_id}")

            # 获取组合的所有日度净值
            nav_history = self.get_nav_history(portfolio_id)

            if not nav_history or len(nav_history) == 0:
                logger.warning(f"组合 {portfolio_id} 没有净值历史数据")
                return 0

            # 转换为 DataFrame
            df = pd.DataFrame([
                {
                    'date': nav.nav_date,
                    'total_assets': float(nav.total_assets),
                    'cumulative_return': float(nav.cumulative_return) if nav.cumulative_return else 0,
                    'cumulative_return_rate': float(nav.cumulative_return_rate) if nav.cumulative_return_rate else 0
                }
                for nav in nav_history
            ])

            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

            # 按周重采样，取每周最后一个交易日
            weekly_df = df.resample('W-FRI').last()
            weekly_df = weekly_df.dropna()

            if len(weekly_df) == 0:
                logger.warning(f"组合 {portfolio_id} 没有周度数据")
                return 0

            # 计算初始资产（第一个净值记录的总资产）
            initial_assets = float(nav_history[0].total_assets)

            # 准备周度净值数据
            weekly_navs = []
            for date, row in weekly_df.iterrows():
                total_assets = float(row['total_assets'])
                # 计算单位净值（以初始资产为基准）
                unit_nav = total_assets / initial_assets if initial_assets > 0 else 1.0
                accum_nav = unit_nav  # 对于实盘组合，单位净值=累计净值
                total_return = float(row['cumulative_return_rate'])

                weekly_navs.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'unit_nav': unit_nav,
                    'accum_nav': accum_nav,
                    'total_return': total_return,
                    'total_value': total_assets
                })

            # 保存到统一的 PortfolioNav 表
            nav_service = PortfolioNavService()
            saved_count = nav_service.save_portfolio_nav_batch(
                db=self.db,
                portfolio_type='live',
                portfolio_id=portfolio_id,
                portfolio_name=portfolio.portfolio_name,
                nav_data=weekly_navs
            )

            logger.info(f"实盘组合 {portfolio.portfolio_name} (ID: {portfolio_id}) 保存了 {saved_count} 条周度净值")
            return saved_count

        except Exception as e:
            logger.error(f"计算并保存周度净值失败: {str(e)}", exc_info=True)
            raise
