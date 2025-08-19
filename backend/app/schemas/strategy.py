"""
策略相关的Pydantic模型
Strategy-related Pydantic models
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum
import re


class MainStrategyEnum(str, Enum):
    """大类策略枚举（仅用于文档示例，实际支持任意字符串）"""
    GROWTH = "成长策略"
    STABLE = "稳健策略" 
    TAIL_HEDGE = "尾部对冲"


class StrategyCreateUpdate(BaseModel):
    """创建/更新策略的输入模型（存在则更新）"""
    fund_code: str = Field(..., min_length=6, max_length=6, description="基金代码，6位字符")
    main_strategy: str = Field(..., min_length=1, max_length=50, description="大类策略，支持任意分类")
    sub_strategy: str = Field(..., min_length=1, max_length=50, description="细分策略，文本输入")
    is_qd: bool = Field(False, description="是否QD产品，默认false")
    
    @validator('fund_code')
    def validate_fund_code(cls, v):
        """验证基金代码：必须6位字符（字母+数字）"""
        if not v or not v.strip():
            raise ValueError('基金代码不能为空')
        
        fund_code = v.strip().upper()
        
        # 检查长度
        if len(fund_code) != 6:
            raise ValueError('基金代码必须是6位字符')
            
        # 检查格式：只允许字母和数字
        if not re.match(r'^[A-Z0-9]{6}$', fund_code):
            raise ValueError('基金代码只能包含字母和数字')
            
        return fund_code
    
    @validator('sub_strategy')
    def validate_sub_strategy(cls, v):
        """验证细分策略"""
        if not v or not v.strip():
            raise ValueError('细分策略不能为空')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "fund_code": "L03126",
                "main_strategy": "成长策略",
                "sub_strategy": "主观多头",
                "is_qd": False
            }
        }


class StrategyResponse(BaseModel):
    """策略记录响应模型 - 完整策略JSON（含所有字段）"""
    fund_code: str
    fund_name: Optional[str] = None
    main_strategy: str
    sub_strategy: str
    is_qd: bool
    
    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """策略列表响应模型 - 按新格式返回"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    data: List[StrategyResponse] = Field(..., description="策略数据列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "data": [
                    {
                        "fund_code": "L03126",
                        "fund_name": "歌斐全球价值配置基金",
                        "main_strategy": "成长策略",
                        "sub_strategy": "主观多头",
                        "is_qd": False
                    }
                ]
            }
        }


class StrategyCreateResponse(BaseModel):
    """创建/更新策略响应模型"""
    action: str = Field(..., description="操作类型：created/updated")
    fund_code: str = Field(..., description="基金代码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "created",
                "fund_code": "L03126"
            }
        }


class StrategyErrorResponse(BaseModel):
    """策略错误响应模型"""
    error: str = Field(..., description="错误信息")
    fund_code: Optional[str] = Field(None, description="相关基金代码")
    detail: str = Field(..., description="错误详情")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "策略不存在",
                "fund_code": "INVALID",
                "detail": "请检查基金代码是否正确"
            }
        }