"""
净值管理路由
Nav Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging

from ..database import get_db
from ..schemas.nav import (
    NavManualCreate, NavResponse, NavListResponse, NavUploadResponse,
    NavDeleteRequest, NavDeleteResponse, NavSearchParams
)
from ..schemas.common import APIResponse, ErrorResponse
from ..services.nav_service import NavService
from ..models import Nav, Fund

logger = logging.getLogger(__name__)

# 创建净值管理路由器
router = APIRouter(
    prefix="/api/nav",
    tags=["净值管理"],
    responses={
        404: {"model": ErrorResponse, "description": "资源未找到"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)


@router.post("/upload", response_model=APIResponse, summary="多文件净值上传")
async def upload_nav_files(
    files: List[UploadFile] = File(..., description="Excel净值文件列表"),
    db: Session = Depends(get_db)
):
    """
    批量上传Excel净值文件
    
    - **files**: Excel文件列表，支持.xlsx格式
    - **自动去重**: 同一基金+日期组合仅保留最新记录
    - **返回**: 处理统计信息和错误详情
    
    Excel文件格式要求：
    - fund_code: 基金代码
    - nav_date: 净值日期
    - unit_nav: 单位净值
    - accum_nav: 累计净值
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少上传一个文件"
        )
    
    nav_service = NavService(db)
    total_results = {
        "success_count": 0,
        "failed_count": 0,
        "updated_count": 0,
        "created_count": 0,
        "errors": [],
        "processed_files": []
    }
    
    try:
        for file in files:
            # 验证文件类型
            if not file.filename.endswith(('.xlsx', '.xls')):
                total_results["errors"].append(f"文件 {file.filename} 不是Excel格式")
                continue
            
            # 读取文件内容
            file_content = await file.read()
            
            # 处理单个文件
            result = nav_service.process_excel_upload(file_content, file.filename)
            
            # 累计统计
            total_results["success_count"] += result.success_count
            total_results["failed_count"] += result.failed_count
            total_results["updated_count"] += result.updated_count
            total_results["created_count"] += result.created_count
            total_results["errors"].extend([f"{file.filename}: {error}" for error in result.errors])
            
            total_results["processed_files"].append({
                "filename": file.filename,
                "success_count": result.success_count,
                "failed_count": result.failed_count
            })
            
            logger.info(f"文件 {file.filename} 处理完成: 成功{result.success_count}, 失败{result.failed_count}")
        
        return APIResponse(
            success=True,
            message=f"文件上传处理完成，成功{total_results['success_count']}条，失败{total_results['failed_count']}条",
            data=total_results
        )
        
    except Exception as e:
        logger.error(f"净值文件上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


@router.post("/manual", response_model=APIResponse, summary="手动添加净值记录")
async def create_nav_manual(
    nav_data: NavManualCreate,
    db: Session = Depends(get_db)
):
    """
    手动添加单条净值记录
    
    - **fund_code**: 基金代码
    - **nav_date**: 净值日期，支持多种格式
    - **unit_nav**: 单位净值，必须大于0
    - **accum_nav**: 累计净值，必须大于等于单位净值
    - **自动去重**: 如存在相同基金+日期记录则更新
    """
    try:
        nav_service = NavService(db)
        nav_record, is_created = nav_service.create_or_update_nav(nav_data)
        
        action = "创建" if is_created else "更新"
        
        return APIResponse(
            success=True,
            message=f"净值记录{action}成功",
            data={
                "nav_record": NavResponse.from_orm(nav_record),
                "action": action,
                "is_created": is_created
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"手动添加净值记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加净值记录失败: {str(e)}"
        )


@router.get("/list", response_model=NavListResponse, summary="获取净值列表")
async def get_nav_list(
    fund_code: Optional[str] = Query(None, description="基金代码筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=1000, description="每页记录数"),
    sort_by: Optional[str] = Query("nav_date", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向(asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    获取净值记录列表（支持分页和筛选）
    
    - **fund_code**: 可选，按基金代码筛选
    - **start_date**: 可选，开始日期筛选
    - **end_date**: 可选，结束日期筛选
    - **page**: 页码，从1开始
    - **page_size**: 每页记录数，最大1000
    """
    try:
        nav_service = NavService(db)
        nav_records, total = nav_service.get_nav_list(
            fund_code=fund_code,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # 转换为响应模型
        nav_responses = []
        for nav in nav_records:
            nav_response = NavResponse.from_orm(nav)
            nav_response.fund_name = nav.fund.fund_name if nav.fund else None
            nav_responses.append(nav_response)
        
        return NavListResponse(
            nav_records=nav_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取净值列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取净值列表失败: {str(e)}"
        )


@router.delete("/{nav_id}", response_model=APIResponse, summary="删除单个净值记录")
async def delete_single_nav_record(
    nav_id: int,
    db: Session = Depends(get_db)
):
    """
    删除单个净值记录
    
    - **nav_id**: 要删除的净值记录ID
    """
    try:
        nav_service = NavService(db)
        deleted_count, errors = nav_service.delete_nav_records([nav_id])
        
        if deleted_count > 0:
            return APIResponse(
                success=True,
                message="净值记录删除成功",
                data={"deleted_id": nav_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"净值记录 ID={nav_id} 不存在"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除净值记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除净值记录失败: {str(e)}"
        )


@router.delete("/", response_model=NavDeleteResponse, summary="批量删除净值记录")
async def delete_nav_records(
    delete_request: NavDeleteRequest,
    db: Session = Depends(get_db)
):
    """
    批量删除净值记录
    
    - **nav_ids**: 要删除的净值记录ID列表
    - **返回**: 删除统计信息和错误详情
    """
    try:
        nav_service = NavService(db)
        deleted_count, errors = nav_service.delete_nav_records(delete_request.nav_ids)
        
        return NavDeleteResponse(
            deleted_count=deleted_count,
            requested_count=len(delete_request.nav_ids),
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"删除净值记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除净值记录失败: {str(e)}"
        )


@router.get("/latest/{fund_code}", response_model=APIResponse, summary="获取指定基金最新净值")
async def get_latest_nav(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    获取指定基金的最新净值记录
    
    - **fund_code**: 基金代码
    """
    try:
        nav_service = NavService(db)
        nav_records = nav_service.get_nav_by_fund(fund_code, limit=1)
        
        if not nav_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {fund_code} 没有净值数据"
            )
        
        latest_nav = nav_records[0]
        nav_response = NavResponse.from_orm(latest_nav)
        nav_response.fund_name = latest_nav.fund.fund_name if latest_nav.fund else None
        
        return APIResponse(
            success=True,
            message=f"获取基金 {fund_code} 最新净值成功",
            data=nav_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基金最新净值失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基金最新净值失败: {str(e)}"
        )


@router.get("/fund/{fund_code}", response_model=APIResponse, summary="获取指定基金净值")
async def get_nav_by_fund(
    fund_code: str,
    limit: int = Query(10, ge=1, le=100, description="返回记录数限制"),
    db: Session = Depends(get_db)
):
    """
    获取指定基金的最新净值记录
    
    - **fund_code**: 基金代码
    - **limit**: 返回记录数量，默认10条
    """
    try:
        nav_service = NavService(db)
        nav_records = nav_service.get_nav_by_fund(fund_code, limit)
        
        if not nav_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {fund_code} 没有净值数据"
            )
        
        nav_responses = [NavResponse.from_orm(nav) for nav in nav_records]
        
        return APIResponse(
            success=True,
            message=f"获取基金 {fund_code} 净值数据成功",
            data={
                "fund_code": fund_code,
                "nav_records": nav_responses,
                "count": len(nav_responses)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基金净值失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基金净值失败: {str(e)}"
        )


@router.get("/statistics/{fund_code}", response_model=APIResponse, summary="获取净值统计")
async def get_nav_statistics(
    fund_code: str,
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取指定基金的净值统计信息
    
    - **fund_code**: 基金代码
    - **days**: 统计天数，默认30天
    - **返回**: 包含收益率、波动率等统计指标
    """
    try:
        nav_service = NavService(db)
        statistics = nav_service.calculate_nav_statistics(fund_code, days)
        
        if "error" in statistics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=statistics["error"]
            )
        
        return APIResponse(
            success=True,
            message=f"获取基金 {fund_code} 统计信息成功",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取净值统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取净值统计失败: {str(e)}"
        )


@router.get("/funds", response_model=APIResponse, summary="获取有净值数据的基金列表")
async def get_funds_with_nav(db: Session = Depends(get_db)):
    """
    获取所有有净值数据的基金列表
    用于前端基金选择器
    """
    try:
        # 查询有净值数据的基金
        funds_with_nav = db.query(Fund).join(Nav).distinct().all()
        
        fund_list = [
            {
                "fund_code": fund.fund_code,
                "fund_name": fund.fund_name,
                "latest_nav_date": db.query(Nav.nav_date)
                                    .filter(Nav.fund_code == fund.fund_code)
                                    .order_by(Nav.nav_date.desc())
                                    .first()[0].isoformat() if db.query(Nav)
                                    .filter(Nav.fund_code == fund.fund_code)
                                    .first() else None
            }
            for fund in funds_with_nav
        ]
        
        return APIResponse(
            success=True,
            message="获取基金列表成功",
            data={
                "funds": fund_list,
                "count": len(fund_list)
            }
        )
        
    except Exception as e:
        logger.error(f"获取基金列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基金列表失败: {str(e)}"
        )