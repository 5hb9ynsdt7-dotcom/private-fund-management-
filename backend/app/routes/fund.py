"""
基金管理路由
Fund Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from ..schemas.common import APIResponse
from ..models import Fund, Nav

logger = logging.getLogger(__name__)

# 创建基金管理路由器
router = APIRouter(
    prefix="/api/funds",
    tags=["基金管理"],
)


@router.delete("/{fund_code}", response_model=APIResponse, summary="删除基金")
async def delete_fund(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    删除指定基金及其所有净值数据

    - **fund_code**: 基金代码

    返回:
        删除结果
    """
    try:
        # 查找基金
        fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()

        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {fund_code} 不存在"
            )

        # 删除该基金的所有净值记录
        deleted_navs = db.query(Nav).filter(Nav.fund_code == fund_code).delete()

        # 删除基金本身
        db.delete(fund)
        db.commit()

        logger.info(f"删除基金 {fund_code}，同时删除了 {deleted_navs} 条净值记录")

        return APIResponse(
            success=True,
            message=f"成功删除基金 {fund_code} 及其 {deleted_navs} 条净值记录",
            data={
                'fund_code': fund_code,
                'deleted_nav_count': deleted_navs
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除基金失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除基金失败: {str(e)}"
        )
