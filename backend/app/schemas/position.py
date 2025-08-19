"""
持仓相关的Pydantic模型
Position-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import date
from typing import List, Optional, Union
import pandas as pd


class PositionResponse(BaseModel):
    """持仓记录响应模型"""
    id: int
    group_id: str
    fund_code: str
    stock_date: date
    cost_with_fee: Optional[Decimal]
    cost_without_fee: Optional[Decimal] 
    shares: Optional[Decimal]
    
    # 关联信息
    client_name: Optional[str] = None
    fund_name: Optional[str] = None
    domestic_planner: Optional[str] = None
    
    class Config:
        from_attributes = True


class PositionListResponse(BaseModel):
    """持仓列表响应模型"""
    positions: List[PositionResponse]
    total: int
    page: int
    page_size: int


class PositionAnalysis(BaseModel):
    """持仓分析结果模型"""
    group_id: str
    fund_code: str
    client_name: Optional[str]
    fund_name: Optional[str]
    
    # 持仓基本信息
    total_cost_with_fee: Decimal
    total_cost_without_fee: Decimal
    total_shares: Decimal
    position_records: int
    
    # 最新净值信息
    latest_nav: Optional[Decimal] = None
    latest_nav_date: Optional[date] = None
    
    # 收益分析
    current_market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    return_rate: Optional[float] = None
    
    # 费用分析
    total_fees: Optional[Decimal] = None
    fee_rate: Optional[float] = None


class ClientPositionSummary(BaseModel):
    """客户持仓汇总模型"""
    group_id: str
    client_name: Optional[str]
    domestic_planner: Optional[str]
    
    # 汇总统计
    total_funds: int
    total_cost_with_fee: Decimal
    total_cost_without_fee: Decimal
    total_current_value: Optional[Decimal] = None
    total_unrealized_pnl: Optional[Decimal] = None
    overall_return_rate: Optional[float] = None
    
    # 持仓明细
    fund_positions: List[PositionAnalysis]


class FundPositionSummary(BaseModel):
    """基金持仓汇总模型"""
    fund_code: str
    fund_name: Optional[str]
    
    # 汇总统计
    total_clients: int
    total_cost_with_fee: Decimal
    total_cost_without_fee: Decimal
    total_shares: Decimal
    
    # 净值信息
    latest_nav: Optional[Decimal] = None
    latest_nav_date: Optional[date] = None
    total_market_value: Optional[Decimal] = None
    
    # 客户分布
    client_positions: List[PositionAnalysis]


class PositionSearchParams(BaseModel):
    """持仓查询参数模型"""
    group_id: Optional[str] = Field(None, description="客户集团号")
    fund_code: Optional[str] = Field(None, description="基金代码")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    domestic_planner: Optional[str] = Field(None, description="理财师")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=1000, description="每页记录数")


class TopHoldersResponse(BaseModel):
    """基金前十大持有人响应模型"""
    fund_code: str
    fund_name: Optional[str]
    total_holders: int
    total_market_value: Optional[Decimal]
    
    top_holders: List[dict] = Field(..., description="前十大持有人列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fund_code": "L03126",
                "fund_name": "示例基金",
                "total_holders": 25,
                "total_market_value": 50000000.00,
                "top_holders": [
                    {
                        "rank": 1,
                        "group_id": "000319506",
                        "client_name": "邢*东",
                        "shares": 1000000.00,
                        "market_value": 1258000.00,
                        "percentage": 25.16
                    }
                ]
            }
        }


class PositionConcentrationAnalysis(BaseModel):
    """持仓集中度分析模型"""
    fund_code: str
    fund_name: Optional[str]
    
    # 集中度指标
    total_clients: int
    herfindahl_index: float = Field(..., description="赫芬达尔指数")
    top5_concentration: float = Field(..., description="前5名集中度")
    top10_concentration: float = Field(..., description="前10名集中度")
    
    # 分布统计
    large_holder_count: int = Field(..., description="大额持有人数量(>100万)")
    medium_holder_count: int = Field(..., description="中等持有人数量(10-100万)")
    small_holder_count: int = Field(..., description="小额持有人数量(<10万)")


class PositionRiskMetrics(BaseModel):
    """持仓风险指标模型"""
    fund_code: str
    fund_name: Optional[str]
    
    # 流动性风险
    total_market_value: Decimal
    avg_position_size: Decimal
    max_position_size: Decimal
    position_size_std: float
    
    # 客户集中度风险
    client_concentration_risk: str = Field(..., description="客户集中度风险等级")
    top5_client_ratio: float
    
    # 历史波动性
    nav_volatility: Optional[float] = Field(None, description="净值波动率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤")
    
    # 风险评级
    overall_risk_level: str = Field(..., description="综合风险等级")


class ClientPortfolioSummary(BaseModel):
    """客户组合汇总"""
    group_id: str = Field(..., description="集团号")
    client_name: Optional[str] = Field(None, description="客户姓名（遮蔽）")
    domestic_planner: Optional[str] = Field(None, description="国内理财师")
    total_cost: Decimal = Field(0, description="总成本")
    total_market_value: Decimal = Field(0, description="总市值")
    total_unrealized_pnl: Decimal = Field(0, description="总浮动盈亏")
    unrealized_pnl_ratio: Decimal = Field(0, description="总盈亏比例")
    position_count: int = Field(0, description="持仓数量")
    fund_count: int = Field(0, description="基金种类数量")
    latest_update: Optional[date] = Field(None, description="最新更新日期")


class ClientListResponse(BaseModel):
    """客户列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    data: List[ClientPortfolioSummary] = Field(..., description="客户组合数据列表")


class EnhancedPositionResponse(BaseModel):
    """增强持仓记录响应模型"""
    id: int
    group_id: str
    fund_code: str
    fund_name: Optional[str]
    first_buy_date: date  # 首次买入日期
    cost_with_fee: Optional[Decimal]  # 持仓成本(含费)
    cost_without_fee: Optional[Decimal]  # 投资金额(不含费)
    shares: Optional[Decimal]  # 持仓份额
    
    # 计算字段
    buy_nav: Optional[Decimal] = None  # 买入净值 = 投资金额(不含费)/持仓份额
    
    # 净值信息
    latest_nav: Optional[Decimal] = None
    latest_nav_date: Optional[date] = None
    
    # 收益信息
    current_market_value: Optional[Decimal] = None
    total_dividends: Optional[Decimal] = None  # 累计分红
    holding_return: Optional[Decimal] = None   # 持有收益 = 最新净值*持仓份额-持仓成本(含费)
    holding_return_rate: Optional[Decimal] = None  # 持有收益率 = 持有收益/持仓成本(含费)
    period_return: Optional[Decimal] = None   # 阶段收益
    
    # 策略信息
    major_strategy: Optional[str] = None
    sub_strategy: Optional[str] = None
    is_qd: Optional[bool] = None  # 是否QD产品
    
    class Config:
        from_attributes = True


class StrategyDistribution(BaseModel):
    """策略分布统计"""
    strategy_name: str
    position_count: int
    total_market_value: Decimal
    percentage: float


class PositionDetailResponse(BaseModel):
    """持仓详情响应模型"""
    client_info: ClientPortfolioSummary
    positions: List[EnhancedPositionResponse]
    
    # 收益概览
    revenue_overview: dict = Field(..., description="收益概览卡片数据")
    
    # 策略分布
    holding_distribution: List[StrategyDistribution] = Field(default_factory=list, description="持仓分布")
    major_strategy_distribution: List[StrategyDistribution] = Field(default_factory=list, description="大类策略分布") 
    sub_strategy_distribution: List[StrategyDistribution] = Field(default_factory=list, description="细分策略分布")
    
    # 分组持仓明细（按策略分组）
    grouped_positions: dict = Field(default_factory=dict, description="按策略分组的持仓明细")