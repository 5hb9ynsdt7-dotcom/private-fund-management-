"""
分红相关的Pydantic模型
Dividend-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date
from decimal import Decimal


class DividendBase(BaseModel):
    """分红基础模型"""
    fund_code: str = Field(..., min_length=1, max_length=20, description="基金代码")
    dividend_date: date = Field(..., description="分红发放日期")
    dividend_per_share: Decimal = Field(..., gt=0, description="每份分红金额")
    ex_dividend_date: Optional[date] = Field(None, description="除息日")
    record_date: Optional[date] = Field(None, description="登记日")
    
    @validator('dividend_date', 'ex_dividend_date', 'record_date')
    def validate_dates(cls, v):
        """验证日期不能是未来日期"""
        if v and v > date.today():
            raise ValueError('日期不能是未来日期')
        return v


class DividendCreate(DividendBase):
    """创建分红的输入模型"""
    pass


class DividendUpdate(BaseModel):
    """更新分红的输入模型"""
    dividend_per_share: Optional[Decimal] = Field(None, gt=0, description="每份分红金额")
    ex_dividend_date: Optional[date] = Field(None, description="除息日")
    record_date: Optional[date] = Field(None, description="登记日")


class DividendResponse(DividendBase):
    """分红响应模型"""
    id: int
    fund_name: Optional[str] = Field(None, description="基金名称")
    
    class Config:
        from_attributes = True


class DividendListResponse(BaseModel):
    """分红列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    data: List[DividendResponse] = Field(..., description="分红数据列表")


class DividendUploadResponse(BaseModel):
    """分红上传响应模型"""
    success_count: int = Field(0, description="成功处理记录数")
    failed_count: int = Field(0, description="失败记录数")
    updated_count: int = Field(0, description="更新记录数")
    created_count: int = Field(0, description="新增记录数")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    processed_files: List[dict] = Field(default_factory=list, description="处理文件列表")


class ClientDividendSummary(BaseModel):
    """客户分红汇总模型"""
    group_id: str = Field(..., description="客户集团号")
    client_name: Optional[str] = Field(None, description="客户姓名（遮蔽）")
    fund_code: str = Field(..., description="基金代码")
    fund_name: Optional[str] = Field(None, description="基金名称")
    
    # 分红统计
    total_dividends_received: Decimal = Field(0, description="累计分红收入")
    dividend_count: int = Field(0, description="分红次数")
    latest_dividend_date: Optional[date] = Field(None, description="最新分红日期")
    latest_dividend_amount: Optional[Decimal] = Field(None, description="最新分红金额")
    
    # 持仓信息（用于分红计算）
    current_shares: Optional[Decimal] = Field(None, description="当前持仓份额")
    avg_dividend_yield: Optional[Decimal] = Field(None, description="平均分红收益率")


class FundDividendHistory(BaseModel):
    """基金分红历史模型"""
    fund_code: str = Field(..., description="基金代码")
    fund_name: Optional[str] = Field(None, description="基金名称")
    
    # 分红统计
    total_dividend_payments: int = Field(0, description="总分红次数")
    total_dividend_amount: Decimal = Field(0, description="累计分红总额")
    avg_dividend_per_payment: Decimal = Field(0, description="平均每次分红金额")
    dividend_frequency: Optional[str] = Field(None, description="分红频率")
    
    # 时间范围
    first_dividend_date: Optional[date] = Field(None, description="首次分红日期")
    latest_dividend_date: Optional[date] = Field(None, description="最新分红日期")
    
    # 分红详情
    dividend_history: List[DividendResponse] = Field(default_factory=list, description="分红历史记录")


class DividendAnalysisRequest(BaseModel):
    """分红分析请求模型"""
    group_id: Optional[str] = Field(None, description="客户集团号")
    fund_code: Optional[str] = Field(None, description="基金代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")


class DividendAnalysisResponse(BaseModel):
    """分红分析响应模型"""
    period: dict = Field(..., description="分析期间")
    total_dividend_income: Decimal = Field(0, description="期间分红收入")
    dividend_payment_count: int = Field(0, description="分红次数")
    avg_dividend_yield: Optional[Decimal] = Field(None, description="平均分红收益率")
    
    # 按基金分组
    fund_dividends: List[dict] = Field(default_factory=list, description="按基金分组的分红统计")
    
    # 按月度分组
    monthly_dividends: List[dict] = Field(default_factory=list, description="按月度分组的分红统计")


class DividendImpactAnalysis(BaseModel):
    """分红对收益影响分析"""
    group_id: str = Field(..., description="客户集团号")
    fund_code: str = Field(..., description="基金代码")
    analysis_period: dict = Field(..., description="分析期间")
    
    # 收益分解
    total_return: Decimal = Field(..., description="总收益")
    capital_gain: Decimal = Field(..., description="资本利得")
    dividend_income: Decimal = Field(..., description="分红收入")
    dividend_contribution: Decimal = Field(..., description="分红贡献度(%)")
    
    # 分红再投资假设
    reinvestment_assumption: dict = Field(..., description="分红再投资假设下的收益")
    
    class Config:
        json_schema_extra = {
            "example": {
                "group_id": "000319506",
                "fund_code": "L03126",
                "analysis_period": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                },
                "total_return": 125800.00,
                "capital_gain": 100000.00,
                "dividend_income": 25800.00,
                "dividend_contribution": 20.51,
                "reinvestment_assumption": {
                    "additional_return": 15000.00,
                    "total_return_with_reinvestment": 140800.00
                }
            }
        }


class ClientDividendBase(BaseModel):
    """客户分红记录基础模型"""
    group_id: str = Field(..., min_length=1, max_length=20, description="客户集团号")
    fund_code: str = Field(..., min_length=1, max_length=20, description="基金代码")
    transaction_type: str = Field(..., description="交易类型：现金红利/红利转投")
    confirmed_amount: Optional[Decimal] = Field(None, description="确认金额(原币)")
    confirmed_shares: Optional[Decimal] = Field(None, description="确认份额")
    confirmed_date: date = Field(..., description="确认日期")
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        """验证交易类型"""
        valid_types = ['现金红利', '红利转投']
        if v not in valid_types:
            raise ValueError(f'交易类型必须是: {", ".join(valid_types)}')
        return v
    
    @validator('confirmed_date')
    def validate_confirmed_date(cls, v):
        """验证确认日期不能是未来日期"""
        if v and v > date.today():
            raise ValueError('确认日期不能是未来日期')
        return v


class ClientDividendCreate(ClientDividendBase):
    """创建客户分红记录的输入模型"""
    pass


class ClientDividendResponse(ClientDividendBase):
    """客户分红记录响应模型"""
    id: int
    
    # 关联信息
    client_name: Optional[str] = None
    fund_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ClientDividendListResponse(BaseModel):
    """客户分红记录列表响应模型"""
    total: int
    page: int
    page_size: int
    data: List[ClientDividendResponse]


class ClientDividendUploadResponse(BaseModel):
    """客户分红记录上传响应模型"""
    success_count: int = Field(..., description="成功处理的记录数")
    failed_count: int = Field(..., description="失败的记录数")
    updated_count: int = Field(..., description="更新的记录数")
    created_count: int = Field(..., description="新增的记录数")
    errors: List[str] = Field(default_factory=list, description="错误详情")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 8,
                "failed_count": 2,
                "updated_count": 1,
                "created_count": 7,
                "errors": [
                    "第2行：交易类型格式错误",
                    "第5行：确认日期不能是未来日期"
                ]
            }
        }