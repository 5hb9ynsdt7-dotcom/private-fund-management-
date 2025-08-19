"""
净值相关的Pydantic模型
Nav-related Pydantic models for data validation
"""

from pydantic import BaseModel, Field, validator
from decimal import Decimal
from datetime import date
from typing import List, Optional, Union
import re


class NavManualCreate(BaseModel):
    """手动添加净值记录的输入模型"""
    fund_code: str = Field(..., min_length=1, max_length=20, description="基金代码")
    fund_name: Optional[str] = Field(None, max_length=100, description="基金名称（可选，用于自动创建基金）")
    nav_date: Union[str, date] = Field(..., description="净值日期，支持多种格式")
    unit_nav: Decimal = Field(..., gt=0, description="单位净值，必须大于0")
    accum_nav: Decimal = Field(..., gt=0, description="累计净值，必须大于0")
    
    @validator('fund_code')
    def validate_fund_code(cls, v):
        """验证基金代码格式"""
        if not v or not v.strip():
            raise ValueError('基金代码不能为空')
        # 只允许字母和数字
        if not re.match(r'^[A-Za-z0-9]+$', v.strip()):
            raise ValueError('基金代码只能包含字母和数字')
        return v.strip().upper()
    
    @validator('accum_nav')
    def validate_accum_nav(cls, v, values):
        """验证累计净值必须大于等于单位净值"""
        if 'unit_nav' in values and v < values['unit_nav']:
            raise ValueError('累计净值必须大于等于单位净值')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "fund_code": "L03126",
                "nav_date": "2025-07-01",
                "unit_nav": 1.2580,
                "accum_nav": 1.2580
            }
        }


class NavResponse(BaseModel):
    """净值记录响应模型"""
    id: int
    fund_code: str
    nav_date: date
    unit_nav: Decimal
    accum_nav: Decimal
    fund_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class NavListResponse(BaseModel):
    """净值列表响应模型"""
    nav_records: List[NavResponse]
    total: int
    page: int
    page_size: int


class NavUploadResponse(BaseModel):
    """净值上传响应模型"""
    success_count: int = Field(..., description="成功处理的记录数")
    failed_count: int = Field(..., description="失败的记录数")
    updated_count: int = Field(..., description="更新的记录数")
    created_count: int = Field(..., description="新增的记录数")
    errors: List[str] = Field(default_factory=list, description="错误详情")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success_count": 10,
                "failed_count": 2,
                "updated_count": 3,
                "created_count": 7,
                "errors": [
                    "第2行：基金代码格式错误",
                    "第5行：累计净值小于单位净值"
                ]
            }
        }


class NavDeleteRequest(BaseModel):
    """删除净值记录请求模型"""
    nav_ids: List[int] = Field(..., min_items=1, description="要删除的净值记录ID列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nav_ids": [1, 2, 3]
            }
        }


class NavDeleteResponse(BaseModel):
    """删除净值记录响应模型"""
    deleted_count: int = Field(..., description="实际删除的记录数")
    requested_count: int = Field(..., description="请求删除的记录数")
    errors: List[str] = Field(default_factory=list, description="删除失败的记录")


class NavSearchParams(BaseModel):
    """净值查询参数模型"""
    fund_code: Optional[str] = Field(None, description="基金代码筛选")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=1000, description="每页记录数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fund_code": "L03126",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "page": 1,
                "page_size": 50
            }
        }