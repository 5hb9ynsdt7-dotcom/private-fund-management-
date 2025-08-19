"""
通用的Pydantic模型
Common Pydantic models for all routes
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime


class APIResponse(BaseModel):
    """通用API响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "操作成功",
                "data": {"id": 1, "name": "示例数据"},
                "errors": [],
                "timestamp": "2025-07-01T10:00:00"
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="操作失败")
    message: str = Field(..., description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")


class PaginationParams(BaseModel):
    """分页参数模型"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(50, ge=1, le=1000, description="每页记录数，最大1000")


class PaginationResponse(BaseModel):
    """分页响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")
    processing_status: str = Field(..., description="处理状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "nav_data.xlsx",
                "file_size": 1024000,
                "upload_time": "2025-07-01T10:00:00",
                "processing_status": "success"
            }
        }