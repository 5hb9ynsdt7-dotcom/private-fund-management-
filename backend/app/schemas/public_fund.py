"""
公募基金Pydantic模型
Public Fund Pydantic Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
import re


# ========== 公募基金主数据 Schemas ==========

class PublicFundBase(BaseModel):
    """公募基金基础模型"""
    fund_code: str = Field(..., min_length=6, max_length=6, description="基金代码（6位）")
    fund_name: str = Field(..., min_length=1, max_length=100, description="基金全称")
    fund_type: Optional[str] = Field(None, max_length=50, description="基金类型")
    fund_company: Optional[str] = Field(None, max_length=100, description="基金公司")
    fund_manager: Optional[str] = Field(None, max_length=100, description="基金经理")
    establish_date: Optional[date] = Field(None, description="成立日期")
    asset_scale: Optional[Decimal] = Field(None, description="资产规模（亿元）")
    remark: Optional[str] = Field(None, description="备注")

    @validator('fund_code')
    def validate_fund_code(cls, v):
        """验证基金代码：6位数字"""
        if not v or not v.strip():
            raise ValueError('基金代码不能为空')
        fund_code = v.strip()
        if len(fund_code) != 6:
            raise ValueError('基金代码必须是6位字符')
        if not re.match(r'^\d{6}$', fund_code):
            raise ValueError('基金代码必须是6位数字')
        return fund_code


class PublicFundCreate(PublicFundBase):
    """创建公募基金的输入模型"""
    data_source: Optional[str] = Field('manual', description="数据来源")

    class Config:
        json_schema_extra = {
            "example": {
                "fund_code": "000001",
                "fund_name": "华夏成长混合",
                "fund_type": "混合型",
                "fund_company": "华夏基金",
                "fund_manager": "张三",
                "establish_date": "2001-12-18",
                "data_source": "manual"
            }
        }


class PublicFundUpdate(BaseModel):
    """更新公募基金的输入模型"""
    fund_name: Optional[str] = Field(None, min_length=1, max_length=100)
    fund_type: Optional[str] = Field(None, max_length=50)
    fund_company: Optional[str] = Field(None, max_length=100)
    fund_manager: Optional[str] = Field(None, max_length=100)
    establish_date: Optional[date] = None
    asset_scale: Optional[Decimal] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class PublicFundResponse(PublicFundBase):
    """公募基金响应模型"""
    id: int
    is_active: bool
    data_source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicFundListResponse(BaseModel):
    """公募基金列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    data: List[PublicFundResponse] = Field(..., description="基金数据列表")


class PublicFundFetchResponse(BaseModel):
    """自动抓取基金响应模型"""
    success: bool
    fund_code: str
    fund_name: Optional[str] = None
    message: str


# ========== 公募基金净值 Schemas ==========

class PublicFundNavBase(BaseModel):
    """公募基金净值基础模型"""
    fund_code: str = Field(..., min_length=6, max_length=6, description="基金代码")
    nav_date: date = Field(..., description="净值日期")
    unit_nav: Decimal = Field(..., gt=0, description="单位净值（必须>0）")
    accum_nav: Decimal = Field(..., gt=0, description="累计净值（必须>0）")

    @validator('accum_nav')
    def validate_accum_nav(cls, v, values):
        """累计净值必须 >= 单位净值"""
        if 'unit_nav' in values and v < values['unit_nav']:
            raise ValueError('累计净值必须大于等于单位净值')
        return v


class PublicFundNavCreate(PublicFundNavBase):
    """创建净值记录的输入模型"""
    data_source: Optional[str] = Field('manual', description="数据来源")

    class Config:
        json_schema_extra = {
            "example": {
                "fund_code": "000001",
                "nav_date": "2024-12-23",
                "unit_nav": 1.2345,
                "accum_nav": 3.4567,
                "data_source": "manual"
            }
        }


class PublicFundNavResponse(PublicFundNavBase):
    """净值记录响应模型"""
    id: int
    daily_return: Optional[Decimal] = None
    data_source: str
    created_at: datetime

    class Config:
        from_attributes = True


class PublicFundNavListResponse(BaseModel):
    """净值列表响应模型"""
    fund_code: str
    fund_name: Optional[str] = None
    total: int
    data: List[PublicFundNavResponse]


class PublicFundNavUploadResponse(BaseModel):
    """净值上传响应模型"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    created_count: int = Field(..., description="新增数量")
    updated_count: int = Field(..., description="更新数量")
    errors: List[str] = Field(default=[], description="错误列表")


# ========== 公募基金分析 Schemas ==========

class SingleFundAnalysisRequest(BaseModel):
    """单基金分析请求模型"""
    fund_code: str = Field(..., description="基金代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    benchmark_code: Optional[str] = Field(None, description="基准代码（可选）")
    save_result: bool = Field(False, description="是否保存分析结果")


class SingleFundAnalysisResponse(BaseModel):
    """单基金分析响应模型"""
    fund_code: str
    fund_name: str
    period: Dict[str, Any]  # {start_date, end_date, days}
    indicators: Dict[str, Any]  # {total_return, annual_return, volatility, max_drawdown, sharpe_ratio, etc.}
    benchmark_comparison: Optional[Dict[str, Any]] = None
    analysis_id: Optional[int] = None


class BacktestRegularRequest(BaseModel):
    """定投回测请求模型"""
    fund_code: str = Field(..., description="基金代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    invest_amount: Decimal = Field(..., gt=0, description="每次投入金额")
    frequency: str = Field(..., description="定投频率：weekly/monthly")
    day_of_week: Optional[int] = Field(None, ge=1, le=5, description="周几（1-5）")
    day_of_month: Optional[int] = Field(None, ge=1, le=31, description="每月几号")
    save_result: bool = Field(False, description="是否保存结果")

    @validator('frequency')
    def validate_frequency(cls, v):
        if v not in ['weekly', 'monthly']:
            raise ValueError('frequency必须是weekly或monthly')
        return v


class BacktestRegularResponse(BaseModel):
    """定投回测响应模型"""
    fund_code: str
    fund_name: str
    backtest_summary: Dict[str, Any]  # {total_invest, total_shares, final_value, total_return, annual_return, invest_count}
    timeline: List[Dict[str, Any]]  # [{date, invest, nav, shares, cumulative_invest, cumulative_shares, market_value, return_rate}]
    analysis_id: Optional[int] = None


class CorrelationAnalysisRequest(BaseModel):
    """相关性分析请求模型"""
    fund_codes: List[str] = Field(..., min_items=2, description="基金代码列表（至少2个）")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    save_result: bool = Field(False, description="是否保存结果")


class CorrelationAnalysisResponse(BaseModel):
    """相关性分析响应模型"""
    fund_codes: List[str]
    fund_names: List[str]
    correlation_matrix: List[List[float]]  # 相关性矩阵
    analysis_id: Optional[int] = None


class PublicFundAnalysisResponse(BaseModel):
    """分析记录响应模型"""
    id: int
    analysis_type: str
    analysis_name: str
    fund_codes: List[str]
    analysis_params: Dict[str, Any]
    analysis_result: Dict[str, Any]
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PublicFundAnalysisListResponse(BaseModel):
    """分析记录列表响应模型"""
    total: int
    page: int
    page_size: int
    data: List[PublicFundAnalysisResponse]


# ========== 通用响应 Schemas ==========

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    detail: str = Field(..., description="错误详情")
    code: str = Field(..., description="错误码")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = True
    message: str
    data: Optional[Any] = None
