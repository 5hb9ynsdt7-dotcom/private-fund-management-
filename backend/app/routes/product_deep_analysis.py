"""
产品深度分析路由
Product Deep Analysis Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime
import logging

from ..database import get_db
from ..models_product_analysis import ProductSectorAllocation, ProductAnalysisSummary, PositionTypeEnum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/product-deep-analysis", tags=["产品深度分析"])


@router.get("/{product_code}/sector-allocation")
async def get_product_sector_allocation(
    product_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取产品的行业配置数据

    Args:
        product_code: 产品代码，如 L02798
        start_date: 起始日期（可选），格式：YYYY-MM-DD
        end_date: 结束日期（可选），格式：YYYY-MM-DD

    Returns:
        按月份分组的行业配置数据，包含多头和空头
    """
    try:
        # 构建查询
        query = db.query(ProductSectorAllocation).filter(
            ProductSectorAllocation.product_code == product_code
        )

        # 添加日期过滤
        if start_date:
            query = query.filter(ProductSectorAllocation.allocation_date >= start_date)
        if end_date:
            query = query.filter(ProductSectorAllocation.allocation_date <= end_date)

        # 按日期排序
        allocations = query.order_by(ProductSectorAllocation.allocation_date).all()

        if not allocations:
            return {
                "product_code": product_code,
                "data": [],
                "message": "未找到该产品的行业配置数据"
            }

        # 按月份分组数据
        monthly_data = {}
        for allocation in allocations:
            month_key = allocation.allocation_date.strftime('%Y-%m')

            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "date": allocation.allocation_date.strftime('%Y-%m-%d'),
                    "long_positions": [],
                    "short_positions": []
                }

            position_data = {
                "sector_name": allocation.sector_name,
                "allocation_pct": float(allocation.allocation_pct)
            }

            if allocation.position_type == PositionTypeEnum.LONG:
                monthly_data[month_key]["long_positions"].append(position_data)
            else:
                monthly_data[month_key]["short_positions"].append(position_data)

        # 转换为列表并排序
        result = [
            {
                "month": month,
                **data
            }
            for month, data in sorted(monthly_data.items())
        ]

        return {
            "product_code": product_code,
            "data": result,
            "total_months": len(result)
        }

    except Exception as e:
        logger.error(f"获取产品行业配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.get("/{product_code}/analysis-summary")
async def get_product_analysis_summary(
    product_code: str,
    db: Session = Depends(get_db)
):
    """
    获取产品分析摘要

    Args:
        product_code: 产品代码，如 L02798

    Returns:
        产品分析摘要，包含核心亮点、主要风险等
    """
    try:
        summary = db.query(ProductAnalysisSummary).filter(
            ProductAnalysisSummary.product_code == product_code
        ).first()

        if not summary:
            return {
                "product_code": product_code,
                "exists": False,
                "message": "未找到该产品的分析摘要"
            }

        # 收集所有非空的亮点
        highlights = []
        for i in range(1, 6):
            highlight = getattr(summary, f'highlight_{i}', None)
            if highlight:
                highlights.append(highlight)

        # 收集所有非空的风险
        risks = []
        for i in range(1, 4):
            risk = getattr(summary, f'risk_{i}', None)
            if risk:
                risks.append(risk)

        return {
            "product_code": product_code,
            "exists": True,
            "highlights": highlights,
            "risks": risks,
            "strategy_description": summary.strategy_description,
            "analysis_period": {
                "start_date": summary.analysis_start_date.strftime('%Y-%m-%d') if summary.analysis_start_date else None,
                "end_date": summary.analysis_end_date.strftime('%Y-%m-%d') if summary.analysis_end_date else None
            },
            "updated_at": summary.updated_at.strftime('%Y-%m-%d %H:%M:%S') if summary.updated_at else None
        }

    except Exception as e:
        logger.error(f"获取产品分析摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")


@router.post("/{product_code}/analysis-summary")
async def create_or_update_analysis_summary(
    product_code: str,
    highlights: List[str],
    risks: List[str],
    strategy_description: Optional[str] = None,
    analysis_start_date: Optional[str] = None,
    analysis_end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    创建或更新产品分析摘要

    Args:
        product_code: 产品代码
        highlights: 核心亮点列表（最多5个）
        risks: 主要风险列表（最多3个）
        strategy_description: 策略特征描述
        analysis_start_date: 分析起始日期
        analysis_end_date: 分析截止日期
    """
    try:
        # 检查是否已存在
        existing = db.query(ProductAnalysisSummary).filter(
            ProductAnalysisSummary.product_code == product_code
        ).first()

        if existing:
            # 更新现有记录
            for i, highlight in enumerate(highlights[:5], 1):
                setattr(existing, f'highlight_{i}', highlight)
            for i, risk in enumerate(risks[:3], 1):
                setattr(existing, f'risk_{i}', risk)

            existing.strategy_description = strategy_description
            if analysis_start_date:
                existing.analysis_start_date = datetime.strptime(analysis_start_date, '%Y-%m-%d').date()
            if analysis_end_date:
                existing.analysis_end_date = datetime.strptime(analysis_end_date, '%Y-%m-%d').date()

            db.commit()
            return {"success": True, "action": "updated", "product_code": product_code}
        else:
            # 创建新记录
            summary = ProductAnalysisSummary(product_code=product_code)

            for i, highlight in enumerate(highlights[:5], 1):
                setattr(summary, f'highlight_{i}', highlight)
            for i, risk in enumerate(risks[:3], 1):
                setattr(summary, f'risk_{i}', risk)

            summary.strategy_description = strategy_description
            if analysis_start_date:
                summary.analysis_start_date = datetime.strptime(analysis_start_date, '%Y-%m-%d').date()
            if analysis_end_date:
                summary.analysis_end_date = datetime.strptime(analysis_end_date, '%Y-%m-%d').date()

            db.add(summary)
            db.commit()
            return {"success": True, "action": "created", "product_code": product_code}

    except Exception as e:
        db.rollback()
        logger.error(f"创建/更新产品分析摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
