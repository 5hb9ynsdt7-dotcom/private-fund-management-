"""
公募基金实盘组合 Schemas
Public Fund Portfolio Schemas
"""

from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal


# ========== 组合基础 ==========

class PortfolioBase(BaseModel):
    """组合基础模型"""
    portfolio_name: str = Field(..., description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")


class PortfolioCreate(PortfolioBase):
    """创建组合请求（initial_amount由系统自动累加交易金额）"""
    pass


class PortfolioUpdate(BaseModel):
    """更新组合请求"""
    portfolio_name: Optional[str] = Field(None, description="组合名称")
    description: Optional[str] = Field(None, description="组合描述")
    cash_balance: Optional[Decimal] = Field(None, description="现金余额")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PortfolioResponse(BaseModel):
    """组合响应"""
    id: int
    portfolio_name: str
    description: Optional[str] = None
    cash_balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # 计算字段
    total_invested: Optional[Decimal] = Field(None, description="累计投入（买入交易累加）")
    current_value: Optional[Decimal] = Field(None, description="当前总市值")
    total_return: Optional[Decimal] = Field(None, description="累计收益")
    total_return_rate: Optional[Decimal] = Field(None, description="累计收益率%")
    position_count: Optional[int] = Field(None, description="持仓数量")

    class Config:
        from_attributes = True


# ========== 交易记录 ==========

class TransactionBase(BaseModel):
    """交易记录基础模型"""
    fund_code: str = Field(..., description="基金代码")
    transaction_type: str = Field(..., description="交易类型: buy/sell/cash_dividend/reinvest_dividend")
    transaction_date: date = Field(..., description="交易日期")
    amount: Optional[Decimal] = Field(None, description="交易金额（买入/卖出/现金分红必填）")
    shares: Optional[Decimal] = Field(None, description="交易份额（红利再投必填，其他可选）")
    nav: Optional[Decimal] = Field(None, description="交易净值（可选，系统自动获取）")
    fee: Optional[Decimal] = Field(0, description="手续费")
    note: Optional[str] = Field(None, description="备注")


class TransactionCreate(TransactionBase):
    """创建交易请求"""
    pass


class TransactionResponse(TransactionBase):
    """交易响应"""
    id: int
    portfolio_id: int
    fund_name: Optional[str] = Field(None, description="基金名称")
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 持仓 ==========

class PositionResponse(BaseModel):
    """持仓响应"""
    id: int
    portfolio_id: int
    fund_code: str
    fund_name: Optional[str] = Field(None, description="基金名称")
    shares: Decimal
    cost_amount: Decimal
    avg_cost_nav: Optional[Decimal] = Field(None, description="平均成本净值")

    # 实时数据
    current_nav: Optional[Decimal] = Field(None, description="当前净值")
    current_nav_date: Optional[date] = Field(None, description="当前净值日期")
    current_value: Optional[Decimal] = Field(None, description="当前市值")
    profit_loss: Optional[Decimal] = Field(None, description="盈亏金额")
    profit_loss_rate: Optional[Decimal] = Field(None, description="盈亏率%")
    weight: Optional[Decimal] = Field(None, description="持仓权重%")

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 组合净值 ==========

class PortfolioNavResponse(BaseModel):
    """组合净值响应"""
    id: int
    portfolio_id: int
    nav_date: date
    total_market_value: Decimal
    cash_balance: Decimal
    total_assets: Decimal
    daily_return: Optional[Decimal] = None
    cumulative_return: Optional[Decimal] = None
    cumulative_return_rate: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== 组合详情 ==========

class PortfolioDetailResponse(BaseModel):
    """组合详情响应"""
    portfolio: PortfolioResponse
    positions: List[PositionResponse]
    transactions: List[TransactionResponse]
    nav_history: List[PortfolioNavResponse]

    # 组合统计
    summary: dict = Field(default_factory=dict, description="组合统计数据")


# ========== 组合列表 ==========

class PortfolioListResponse(BaseModel):
    """组合列表响应"""
    total: int
    data: List[PortfolioResponse]
