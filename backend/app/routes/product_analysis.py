"""
产品分析路由
Product Analysis Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..schemas.common import APIResponse
from ..services.product_analysis_service import ProductAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/product-analysis",
    tags=["产品分析"],
)


@router.get("/{fund_code}", response_model=APIResponse, summary="获取产品分析")
async def get_product_analysis(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    获取指定产品的全面分析

    - **fund_code**: 产品代码

    返回:
        - 基础指标：累计收益率、年化收益率、最大回撤、波动率、夏普比率等
        - 风险指标：下行风险、索提诺比率、最大连续下跌天数、VAR等
        - 持有期分析：任意时间买入持有6个月、1年、2年的盈利概率和收益情况
        - 月度分析：每月收益情况和月度胜率
        - 净值曲线：净值和回撤曲线数据
    """
    try:
        service = ProductAnalysisService(db)
        analysis_data = service.analyze_product(fund_code)

        return APIResponse(
            success=True,
            message="产品分析获取成功",
            data=analysis_data
        )

    except ValueError as e:
        logger.error(f"产品分析参数错误 {fund_code}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取产品分析失败 {fund_code}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取产品分析失败: {str(e)}"
        )
