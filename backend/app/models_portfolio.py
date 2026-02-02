"""
公募基金实盘组合数据模型
Public Fund Portfolio Models
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from .models import Base


class PublicFundPortfolio(Base):
    """实盘组合表"""
    __tablename__ = "public_fund_portfolio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_name = Column(String(100), nullable=False, comment="组合名称")
    description = Column(Text, nullable=True, comment="组合描述")
    initial_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="初始投入金额")
    cash_balance = Column(Numeric(15, 2), nullable=False, default=0, comment="当前现金余额")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否激活")
    portfolio_type = Column(String(20), nullable=False, default='public', comment="组合类型: public/private")
    update_frequency = Column(String(20), nullable=True, default='daily', comment="更新频率: daily/weekly/monthly")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class PublicFundPortfolioPosition(Base):
    """组合持仓表"""
    __tablename__ = "public_fund_portfolio_position"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('public_fund_portfolio.id', ondelete='CASCADE'), nullable=False, index=True, comment="组合ID")
    fund_code = Column(String(10), ForeignKey('public_fund.fund_code', ondelete='RESTRICT'), nullable=False, index=True, comment="基金代码")
    shares = Column(Numeric(15, 4), nullable=False, default=0, comment="持仓份额")
    cost_amount = Column(Numeric(15, 2), nullable=False, default=0, comment="成本金额")
    avg_cost_nav = Column(Numeric(10, 4), nullable=True, comment="平均成本净值")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class PublicFundPortfolioTransaction(Base):
    """组合交易记录表"""
    __tablename__ = "public_fund_portfolio_transaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('public_fund_portfolio.id', ondelete='CASCADE'), nullable=False, index=True, comment="组合ID")
    fund_code = Column(String(10), ForeignKey('public_fund.fund_code', ondelete='RESTRICT'), nullable=False, index=True, comment="基金代码")
    transaction_type = Column(String(20), nullable=False, comment="交易类型: buy/sell")
    transaction_date = Column(Date, nullable=False, index=True, comment="交易日期")
    amount = Column(Numeric(15, 2), nullable=False, comment="交易金额")
    shares = Column(Numeric(15, 4), nullable=False, comment="交易份额")
    nav = Column(Numeric(10, 4), nullable=True, comment="交易净值")
    fee = Column(Numeric(10, 2), nullable=True, default=0, comment="手续费")
    note = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")


class PublicFundPortfolioNav(Base):
    """组合每日净值表"""
    __tablename__ = "public_fund_portfolio_nav"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey('public_fund_portfolio.id', ondelete='CASCADE'), nullable=False, index=True, comment="组合ID")
    nav_date = Column(Date, nullable=False, index=True, comment="净值日期")
    total_market_value = Column(Numeric(15, 2), nullable=False, comment="持仓总市值")
    cash_balance = Column(Numeric(15, 2), nullable=False, default=0, comment="现金余额")
    total_assets = Column(Numeric(15, 2), nullable=False, comment="总资产 = 市值 + 现金")
    daily_return = Column(Numeric(15, 2), nullable=True, comment="日收益")
    cumulative_return = Column(Numeric(15, 2), nullable=True, comment="累计收益")
    cumulative_return_rate = Column(Numeric(10, 4), nullable=True, comment="累计收益率%")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
