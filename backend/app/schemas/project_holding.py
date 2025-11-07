"""
项目持仓分析模块数据模式定义
Project Holding Analysis Pydantic Schemas
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import date
from decimal import Decimal


class ProjectHoldingAssetBase(BaseModel):
    """项目持仓资产基础模型"""
    project_name: str = Field(..., description="项目名称", max_length=50)
    month: date = Field(..., description="月份")
    a_share_ratio: Optional[Decimal] = Field(None, description="A股比例", ge=0, le=100)
    h_share_ratio: Optional[Decimal] = Field(None, description="H股比例", ge=0, le=100)
    us_share_ratio: Optional[Decimal] = Field(None, description="美股比例", ge=0, le=100)
    other_market_ratio: Optional[Decimal] = Field(None, description="其他市场比例", ge=0, le=100)
    global_bond_ratio: Optional[Decimal] = Field(None, description="全球债券比例", ge=0, le=100)
    convertible_bond_ratio: Optional[Decimal] = Field(None, description="可转债比例", ge=0, le=100)
    other_ratio: Optional[Decimal] = Field(None, description="其他比例", ge=0, le=100)

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """验证月份格式：只保留年月，日期设为1号"""
        return date(v.year, v.month, 1)


class ProjectHoldingAssetCreate(ProjectHoldingAssetBase):
    """项目持仓资产创建模型"""
    pass


class ProjectHoldingAssetUpdate(BaseModel):
    """项目持仓资产更新模型"""
    a_share_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    h_share_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    us_share_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    other_market_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    global_bond_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    convertible_bond_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    other_ratio: Optional[Decimal] = Field(None, ge=0, le=100)


class ProjectHoldingAssetResponse(ProjectHoldingAssetBase):
    """项目持仓资产响应模型"""
    id: int
    stock_total_ratio: Optional[Decimal] = Field(None, description="股票总仓位比例")
    created_at: date

    class Config:
        from_attributes = True


class ProjectHoldingIndustryBase(BaseModel):
    """项目持仓行业基础模型"""
    project_name: str = Field(..., description="项目名称", max_length=50)
    month: date = Field(..., description="月份")
    ratio_type: str = Field(..., description="行业比例计算方式", pattern="^(based_on_stock|based_on_total)$")
    industry1: Optional[str] = Field(None, description="第一持仓行业", max_length=50)
    industry1_ratio: Optional[Decimal] = Field(None, description="第一持仓行业比例（支持负值）")
    industry2: Optional[str] = Field(None, description="第二持仓行业", max_length=50)
    industry2_ratio: Optional[Decimal] = Field(None, description="第二持仓行业比例（支持负值）")
    industry3: Optional[str] = Field(None, description="第三持仓行业", max_length=50)
    industry3_ratio: Optional[Decimal] = Field(None, description="第三持仓行业比例（支持负值）")
    industry4: Optional[str] = Field(None, description="第四持仓行业", max_length=50)
    industry4_ratio: Optional[Decimal] = Field(None, description="第四持仓行业比例（支持负值）")
    industry5: Optional[str] = Field(None, description="第五持仓行业", max_length=50)
    industry5_ratio: Optional[Decimal] = Field(None, description="第五持仓行业比例（支持负值）")

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        """验证月份格式：只保留年月，日期设为1号"""
        return date(v.year, v.month, 1)

    @field_validator('ratio_type')
    @classmethod
    def validate_ratio_type(cls, v):
        """验证比例计算方式"""
        if v not in ['based_on_stock', 'based_on_total']:
            raise ValueError("比例计算方式必须是 'based_on_stock' 或 'based_on_total'")
        return v


class ProjectHoldingIndustryCreate(ProjectHoldingIndustryBase):
    """项目持仓行业创建模型"""
    pass


class ProjectHoldingIndustryUpdate(BaseModel):
    """项目持仓行业更新模型"""
    ratio_type: Optional[str] = Field(None, pattern="^(based_on_stock|based_on_total)$")
    industry1: Optional[str] = Field(None, max_length=50)
    industry1_ratio: Optional[Decimal] = Field(None, description="第一持仓行业比例（支持负值）")
    industry2: Optional[str] = Field(None, max_length=50)
    industry2_ratio: Optional[Decimal] = Field(None, description="第二持仓行业比例（支持负值）")
    industry3: Optional[str] = Field(None, max_length=50)
    industry3_ratio: Optional[Decimal] = Field(None, description="第三持仓行业比例（支持负值）")
    industry4: Optional[str] = Field(None, max_length=50)
    industry4_ratio: Optional[Decimal] = Field(None, description="第四持仓行业比例（支持负值）")
    industry5: Optional[str] = Field(None, max_length=50)
    industry5_ratio: Optional[Decimal] = Field(None, description="第五持仓行业比例（支持负值）")


class ProjectHoldingIndustryResponse(ProjectHoldingIndustryBase):
    """项目持仓行业响应模型"""
    id: int
    created_at: date
    actual_ratios: Optional[Dict[str, float]] = Field(None, description="计算后的实际比例")

    class Config:
        from_attributes = True


class ProjectListItem(BaseModel):
    """项目列表项模型"""
    project_name: str = Field(..., description="项目名称")
    main_strategy: Optional[str] = Field(None, description="主策略")
    sub_strategy: Optional[str] = Field(None, description="子策略")
    latest_data_month: Optional[str] = Field(None, description="最新录入数据月份")
    latest_industries: Optional[List[str]] = Field(None, description="最新行业分类")


class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    projects: List[ProjectListItem] = Field(..., description="项目列表")
    total: int = Field(..., description="项目总数")


class ProjectHoldingDetailResponse(BaseModel):
    """项目持仓详情响应模型"""
    project_name: str = Field(..., description="项目名称")
    asset_records: List[ProjectHoldingAssetResponse] = Field(..., description="资产配置记录")
    industry_records: List[ProjectHoldingIndustryResponse] = Field(..., description="行业配置记录")


class IndustryAnalysisItem(BaseModel):
    """行业分析项模型"""
    month: date = Field(..., description="月份")
    industry_name: str = Field(..., description="行业名称")
    original_ratio: Decimal = Field(..., description="原始比例")
    actual_ratio: Decimal = Field(..., description="实际比例（占总仓位）")
    ratio_type: str = Field(..., description="计算方式")


class ProjectHoldingAnalysisResponse(BaseModel):
    """项目持仓分析响应模型"""
    project_name: str = Field(..., description="项目名称")
    asset_analysis: List[ProjectHoldingAssetResponse] = Field(..., description="资产分析数据")
    industry_analysis: List[IndustryAnalysisItem] = Field(..., description="行业分析数据")


class BulkOperationRequest(BaseModel):
    """批量操作请求模型"""
    ids: List[int] = Field(..., description="记录ID列表")


class BulkOperationResponse(BaseModel):
    """批量操作响应模型"""
    success_count: int = Field(..., description="成功操作数量")
    failed_count: int = Field(..., description="失败操作数量")
    errors: List[str] = Field(default=[], description="错误信息列表")