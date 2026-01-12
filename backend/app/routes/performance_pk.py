"""
业绩PK路由
Performance PK Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..database import get_db
from ..services.performance_pk_service import PerformancePKService
from ..models import Fund, Nav, PerformancePKRecord
from ..models_public_fund import PublicFund
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/performance",
    tags=["业绩PK"],
)


class CompareObject(BaseModel):
    """对比对象"""
    id: str
    type: str  # 'product' or 'portfolio'


class CompareRequest(BaseModel):
    """对比请求"""
    objects: List[CompareObject]
    time_range: str = '1y'  # '1m', '3m', '6m', '1y', '3y', 'all', 'custom'
    custom_range: Optional[List[str]] = None
    benchmark: Optional[str] = None
    align_mode: str = 'common'  # 'common' or 'separate'


class SavePKRequest(BaseModel):
    """保存PK记录请求"""
    title: str
    compare_type: str  # 'product' or 'portfolio'
    objects: List[CompareObject]
    time_range: str
    custom_range: Optional[List[str]] = None
    benchmark: Optional[str] = None
    align_mode: str = 'common'


@router.get("/products", summary="获取所有可对比产品")
async def get_all_products(
    search: str = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    获取所有可对比的产品（私募基金+公募基金）

    返回:
        产品列表，包含私募基金和公募基金
    """
    try:
        products = []

        # 获取有净值数据的私募基金
        private_funds_query = db.query(Fund).join(Nav).distinct()

        if search:
            private_funds_query = private_funds_query.filter(
                (Fund.fund_code.like(f"%{search}%")) |
                (Fund.fund_name.like(f"%{search}%")) |
                (Fund.short_name.like(f"%{search}%"))
            )

        private_funds = private_funds_query.all()

        for fund in private_funds:
            # 获取策略信息
            main_strategy = fund.strategy.main_strategy if fund.strategy else '未分类'

            products.append({
                'id': fund.fund_code,
                'code': fund.fund_code,
                'name': fund.short_name or fund.fund_name,
                'full_name': fund.fund_name,
                'type': 'private',
                'category': main_strategy
            })

        # 获取公募基金
        public_funds_query = db.query(PublicFund)

        if search:
            public_funds_query = public_funds_query.filter(
                (PublicFund.fund_code.like(f"%{search}%")) |
                (PublicFund.fund_name.like(f"%{search}%"))
            )

        public_funds = public_funds_query.limit(100).all()  # 限制数量避免过多

        for fund in public_funds:
            products.append({
                'id': f"public_{fund.fund_code}",
                'code': fund.fund_code,
                'name': fund.fund_name,
                'full_name': fund.fund_name,
                'type': 'public',
                'category': fund.fund_type or '公募基金'
            })

        return {
            'success': True,
            'data': products,
            'count': len(products)
        }

    except Exception as e:
        logger.error(f"获取产品列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取产品列表失败: {str(e)}"
        )


@router.post("/compare", summary="业绩对比分析")
async def compare_performance(
    request: CompareRequest,
    db: Session = Depends(get_db)
):
    """
    业绩对比分析

    - **objects**: 对比对象列表
    - **time_range**: 时间范围
    - **custom_range**: 自定义时间范围
    - **benchmark**: 基准指数代码
    - **align_mode**: 对齐方式

    返回:
        - chart_data: 图表数据
        - metrics: 各项指标对比
    """
    try:
        service = PerformancePKService(db)

        # 转换对象格式
        objects = [
            {'id': obj.id, 'type': obj.type}
            for obj in request.objects
        ]

        result = service.compare_performance(
            objects=objects,
            time_range=request.time_range,
            custom_range=request.custom_range,
            benchmark=request.benchmark,
            align_mode=request.align_mode
        )

        return result

    except ValueError as e:
        logger.error(f"业绩对比参数错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"业绩对比分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"业绩对比分析失败: {str(e)}"
        )


@router.post("/pk/save", summary="保存PK记录")
async def save_pk_record(
    request: SavePKRequest,
    db: Session = Depends(get_db)
):
    """
    保存业绩PK记录

    - **title**: PK标题
    - **compare_type**: 对比类型
    - **objects**: 对比对象列表
    - **time_range**: 时间范围
    - **custom_range**: 自定义时间范围
    - **benchmark**: 基准指数
    - **align_mode**: 对齐模式

    返回:
        保存的记录ID
    """
    try:
        # 创建记录
        record = PerformancePKRecord(
            title=request.title,
            compare_type=request.compare_type,
            objects=json.dumps([obj.dict() for obj in request.objects]),
            time_range=request.time_range,
            custom_range=json.dumps(request.custom_range) if request.custom_range else None,
            benchmark=request.benchmark,
            align_mode=request.align_mode
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(f"保存PK记录成功: ID={record.id}, title='{record.title}'")

        return {
            'success': True,
            'id': record.id,
            'message': 'PK记录保存成功'
        }

    except Exception as e:
        db.rollback()
        logger.error(f"保存PK记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存PK记录失败: {str(e)}"
        )


@router.get("/pk/list", summary="获取PK记录列表")
async def get_pk_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取所有保存的PK记录列表

    返回:
        PK记录列表及分页信息
    """
    try:
        # 查询总数
        total = db.query(PerformancePKRecord).count()

        # 分页查询
        records = db.query(PerformancePKRecord)\
            .order_by(PerformancePKRecord.created_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        # 转换为字典格式
        records_data = []
        for record in records:
            records_data.append({
                'id': record.id,
                'title': record.title,
                'compare_type': record.compare_type,
                'time_range': record.time_range,
                'benchmark': record.benchmark,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            })

        return {
            'success': True,
            'data': records_data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    except Exception as e:
        logger.error(f"获取PK记录列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取PK记录列表失败: {str(e)}"
        )


@router.get("/pk/{pk_id}", summary="获取PK记录详情")
async def get_pk_record(
    pk_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定PK记录的详细信息

    - **pk_id**: PK记录ID

    返回:
        PK记录详细信息
    """
    try:
        record = db.query(PerformancePKRecord).filter(PerformancePKRecord.id == pk_id).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到ID为{pk_id}的PK记录"
            )

        # 解析JSON字段
        objects = json.loads(record.objects)
        custom_range = json.loads(record.custom_range) if record.custom_range else None

        return {
            'success': True,
            'data': {
                'id': record.id,
                'title': record.title,
                'compare_type': record.compare_type,
                'objects': objects,
                'time_range': record.time_range,
                'custom_range': custom_range,
                'benchmark': record.benchmark,
                'align_mode': record.align_mode,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取PK记录详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取PK记录详情失败: {str(e)}"
        )


@router.delete("/pk/{pk_id}", summary="删除PK记录")
async def delete_pk_record(
    pk_id: int,
    db: Session = Depends(get_db)
):
    """
    删除指定的PK记录

    - **pk_id**: PK记录ID

    返回:
        删除结果
    """
    try:
        record = db.query(PerformancePKRecord).filter(PerformancePKRecord.id == pk_id).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到ID为{pk_id}的PK记录"
            )

        db.delete(record)
        db.commit()

        logger.info(f"删除PK记录成功: ID={pk_id}")

        return {
            'success': True,
            'message': 'PK记录删除成功'
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除PK记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除PK记录失败: {str(e)}"
        )
