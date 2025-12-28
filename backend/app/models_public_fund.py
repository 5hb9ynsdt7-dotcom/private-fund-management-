"""
公募基金数据模型
Public Fund Data Models

独立于私募基金系统的公募基金管理模块
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Boolean, Text, UniqueConstraint, Index
from sqlalchemy.sql import func
from datetime import datetime, date
from .models import Base  # 使用与私募系统相同的Base，但表名完全独立


class PublicFund(Base):
    """公募基金主数据表"""
    __tablename__ = "public_fund"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")

    # 基金基本信息（定义性字段）
    fund_code = Column(String(10), unique=True, nullable=False, index=True, comment="基金代码（6位数字）")
    fund_name = Column(String(100), nullable=False, comment="基金全称")
    fund_type = Column(String(50), nullable=True, index=True, comment="基金类型（股票型/债券型/混合型/货币型/QDII等）")
    fund_company = Column(String(100), nullable=True, index=True, comment="基金公司名称")
    fund_manager = Column(String(100), nullable=True, comment="基金经理姓名")
    establish_date = Column(Date, nullable=True, comment="成立日期")

    # 可派生字段
    asset_scale = Column(Numeric(15, 2), nullable=True, comment="最新资产规模（亿元）")

    # 系统字段
    data_source = Column(String(50), default='manual', comment="数据来源（manual/eastmoney/wind等）")
    is_active = Column(Boolean, default=True, comment="是否在运行（用于标记清盘基金）")
    remark = Column(Text, nullable=True, comment="备注信息")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<PublicFund(code={self.fund_code}, name={self.fund_name})>"


class PublicFundNav(Base):
    """公募基金净值表"""
    __tablename__ = "public_fund_nav"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")

    # 净值数据（定义性字段）
    fund_code = Column(String(10), nullable=False, index=True, comment="基金代码")
    nav_date = Column(Date, nullable=False, index=True, comment="净值日期")
    unit_nav = Column(Numeric(10, 4), nullable=False, comment="单位净值")
    accum_nav = Column(Numeric(10, 4), nullable=False, comment="累计净值")

    # 可派生字段
    daily_return = Column(Numeric(10, 6), nullable=True, comment="日收益率（%）")

    # 系统字段
    data_source = Column(String(50), default='manual', comment="数据来源")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    # 联合唯一约束：同一基金同一天只能有一条净值记录
    __table_args__ = (
        UniqueConstraint('fund_code', 'nav_date', name='uq_fund_code_nav_date'),
        Index('idx_fund_code_nav_date', 'fund_code', 'nav_date'),
    )

    def __repr__(self):
        return f"<PublicFundNav(code={self.fund_code}, date={self.nav_date}, nav={self.unit_nav})>"


class PublicFundAnalysis(Base):
    """公募基金分析结果表"""
    __tablename__ = "public_fund_analysis"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")

    # 分析基本信息
    analysis_type = Column(String(50), nullable=False, index=True, comment="分析类型（single_fund/correlation/backtest_regular/backtest_portfolio）")
    analysis_name = Column(String(200), nullable=False, comment="分析名称（用户自定义）")

    # 分析内容（JSON格式）
    fund_codes = Column(Text, nullable=False, comment="涉及的基金代码（JSON数组格式）")
    analysis_params = Column(Text, nullable=False, comment="分析参数（JSON格式）")
    analysis_result = Column(Text, nullable=False, comment="分析结果（JSON格式）")

    # 系统字段
    created_by = Column(String(50), nullable=True, comment="创建人（预留）")
    created_at = Column(DateTime, default=func.now(), index=True, comment="创建时间")

    def __repr__(self):
        return f"<PublicFundAnalysis(id={self.id}, type={self.analysis_type}, name={self.analysis_name})>"
