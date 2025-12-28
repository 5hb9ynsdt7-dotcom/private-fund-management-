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

    # ========== 组合管理 ==========

    def create_portfolio(self, portfolio_data: PortfolioCreate) -> PublicFundPortfolio:
        """
        创建新组合（initial_amount 由买入交易自动累加）
        """
        try:
            portfolio = PublicFundPortfolio(
                portfolio_name=portfolio_data.portfolio_name,
                description=portfolio_data.description,
                initial_amount=Decimal('0'),  # 初始为0，由交易累加
                cash_balance=Decimal('0')     # 不使用，保留字段兼容
            )

            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)

            logger.info(f"创建组合成功: {portfolio.portfolio_name}")
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
        自动从公募基金净值表获取净值，并计算份额
        """
        try:
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"组合 {portfolio_id} 不存在")

            # 验证基金是否存在
            fund = self.db.query(PublicFund).filter(PublicFund.fund_code == transaction_data.fund_code).first()
            if not fund:
                raise ValueError(f"基金 {transaction_data.fund_code} 不存在，请先在公募基金库中添加该基金")

            # 自动获取交易日期的净值（如果未提供）
            nav_value = transaction_data.nav
            if not nav_value:
                # 从公募基金净值表获取最近的净值
                nav_record = self.db.query(PublicFundNav).filter(
                    and_(
                        PublicFundNav.fund_code == transaction_data.fund_code,
                        PublicFundNav.nav_date <= transaction_data.transaction_date
                    )
                ).order_by(desc(PublicFundNav.nav_date)).first()

                if not nav_record:
                    raise ValueError(f"未找到基金 {transaction_data.fund_code} 在 {transaction_data.transaction_date} 或之前的净值数据，请先抓取净值")

                nav_value = nav_record.unit_nav
                logger.info(f"自动获取净值: {transaction_data.fund_code} 日期:{nav_record.nav_date} 净值:{nav_value}")

            # 自动计算份额（如果未提供）
            shares = transaction_data.shares
            if not shares or shares == 0:
                if not transaction_data.amount or transaction_data.amount == 0:
                    raise ValueError("请提供交易金额或交易份额")

                # 根据金额和净值计算份额
                shares = transaction_data.amount / nav_value
                logger.info(f"自动计算份额: 金额:{transaction_data.amount} / 净值:{nav_value} = {shares}")

            # 创建交易记录
            transaction = PublicFundPortfolioTransaction(
                portfolio_id=portfolio_id,
                fund_code=transaction_data.fund_code,
                transaction_type=transaction_data.transaction_type,
                transaction_date=transaction_data.transaction_date,
                amount=transaction_data.amount,
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
                amount=transaction_data.amount,
                shares=shares,
                nav=nav_value,
                fee=transaction_data.fee,
                note=transaction_data.note
            )
            self._update_position(portfolio_id, updated_transaction_data)

            # 更新总投入金额（不使用现金余额概念）
            if transaction_data.transaction_type == 'buy':
                # 买入：增加总投入
                portfolio.initial_amount += transaction_data.amount
            # 卖出不改变总投入

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

            # 回滚总投入（不使用现金余额概念）
            if transaction.transaction_type == 'buy':
                # 回滚买入：减少总投入
                portfolio.initial_amount -= transaction.amount
            # 卖出不改变总投入

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
                # 获取最新净值
                nav_query = self.db.query(PublicFundNav)\
                    .filter(
                        and_(
                            PublicFundNav.fund_code == position.fund_code,
                            PublicFundNav.nav_date <= as_of_date
                        )
                    )\
                    .order_by(desc(PublicFundNav.nav_date))

                latest_nav_record = nav_query.first()

                if latest_nav_record:
                    current_nav = latest_nav_record.unit_nav
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
                        'current_nav_date': latest_nav_record.nav_date,
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
