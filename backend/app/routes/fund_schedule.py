"""
基金档期管理路由
Fund Schedule Management Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from ..database import get_db
from ..schemas.common import APIResponse
from ..models import Fund, FundScheduleRule, Strategy
from ..services.fund_schedule_service import FundScheduleService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/fund-schedules",
    tags=["基金档期管理"],
)

# 创建服务实例
schedule_service = FundScheduleService()


# Pydantic schemas
class FundScheduleRuleCreate(BaseModel):
    """创建/更新档期规则的请求模型"""
    fund_code: str
    subscription_rule: Optional[str] = None
    redemption_rule: Optional[str] = None
    lock_period: Optional[str] = None


class FundScheduleRuleResponse(BaseModel):
    """档期规则响应模型"""
    id: int
    fund_code: str
    fund_name: Optional[str] = None
    subscription_rule: Optional[str] = None
    redemption_rule: Optional[str] = None
    lock_period: Optional[str] = None
    main_strategy: Optional[str] = None
    sub_strategy: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CalculateDatesRequest(BaseModel):
    """计算日期请求模型"""
    fund_code: str
    year: int
    month: int


class CalendarRequest(BaseModel):
    """月历请求模型"""
    fund_codes: List[str]
    year: int
    month: int


@router.post("/rules", response_model=APIResponse, summary="创建或更新档期规则")
async def create_or_update_rule(
    rule_data: FundScheduleRuleCreate,
    db: Session = Depends(get_db)
):
    """
    创建或更新基金档期规则

    - **fund_code**: 基金代码
    - **subscription_rule**: 申购规则描述
    - **redemption_rule**: 赎回规则描述
    - **lock_period**: 锁定期描述
    """
    try:
        # 检查基金是否存在
        fund = db.query(Fund).filter(Fund.fund_code == rule_data.fund_code).first()
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {rule_data.fund_code} 不存在"
            )

        # 查找是否已存在规则
        existing_rule = db.query(FundScheduleRule).filter(
            FundScheduleRule.fund_code == rule_data.fund_code
        ).first()

        if existing_rule:
            # 更新现有规则
            existing_rule.subscription_rule = rule_data.subscription_rule
            existing_rule.redemption_rule = rule_data.redemption_rule
            existing_rule.lock_period = rule_data.lock_period
            existing_rule.updated_at = datetime.now()
            message = f"成功更新基金 {rule_data.fund_code} 的档期规则"
        else:
            # 创建新规则
            new_rule = FundScheduleRule(
                fund_code=rule_data.fund_code,
                subscription_rule=rule_data.subscription_rule,
                redemption_rule=rule_data.redemption_rule,
                lock_period=rule_data.lock_period
            )
            db.add(new_rule)
            message = f"成功创建基金 {rule_data.fund_code} 的档期规则"

        db.commit()

        return APIResponse(
            success=True,
            message=message,
            data={
                "fund_code": rule_data.fund_code,
                "subscription_rule": rule_data.subscription_rule,
                "redemption_rule": rule_data.redemption_rule,
                "lock_period": rule_data.lock_period
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建/更新档期规则失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建/更新档期规则失败: {str(e)}"
        )


@router.get("/rules", response_model=APIResponse, summary="获取所有档期规则")
async def get_all_rules(db: Session = Depends(get_db)):
    """
    获取所有基金的档期规则
    """
    try:
        # 查询所有档期规则，并联表查询基金名称和策略
        rules = db.query(
            FundScheduleRule,
            Fund.fund_name,
            Strategy.main_strategy,
            Strategy.sub_strategy
        ).join(
            Fund, FundScheduleRule.fund_code == Fund.fund_code
        ).outerjoin(
            Strategy, Fund.fund_code == Strategy.fund_code
        ).all()

        result = []
        for rule, fund_name, main_strategy, sub_strategy in rules:
            result.append({
                "id": rule.id,
                "fund_code": rule.fund_code,
                "fund_name": fund_name,
                "subscription_rule": rule.subscription_rule,
                "redemption_rule": rule.redemption_rule,
                "lock_period": rule.lock_period,
                "main_strategy": main_strategy,
                "sub_strategy": sub_strategy,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
            })

        return APIResponse(
            success=True,
            message=f"成功获取 {len(result)} 条档期规则",
            data=result
        )

    except Exception as e:
        logger.error(f"获取档期规则失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取档期规则失败: {str(e)}"
        )


@router.get("/rules/{fund_code}", response_model=APIResponse, summary="获取指定基金的档期规则")
async def get_rule_by_fund(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    获取指定基金的档期规则
    """
    try:
        result = db.query(
            FundScheduleRule,
            Fund.fund_name,
            Strategy.main_strategy,
            Strategy.sub_strategy
        ).join(
            Fund, FundScheduleRule.fund_code == Fund.fund_code
        ).outerjoin(
            Strategy, Fund.fund_code == Strategy.fund_code
        ).filter(
            FundScheduleRule.fund_code == fund_code
        ).first()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到基金 {fund_code} 的档期规则"
            )

        rule, fund_name, main_strategy, sub_strategy = result

        return APIResponse(
            success=True,
            message=f"成功获取基金 {fund_code} 的档期规则",
            data={
                "id": rule.id,
                "fund_code": rule.fund_code,
                "fund_name": fund_name,
                "subscription_rule": rule.subscription_rule,
                "redemption_rule": rule.redemption_rule,
                "lock_period": rule.lock_period,
                "main_strategy": main_strategy,
                "sub_strategy": sub_strategy,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取档期规则失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取档期规则失败: {str(e)}"
        )


@router.delete("/rules/{fund_code}", response_model=APIResponse, summary="删除档期规则")
async def delete_rule(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    删除指定基金的档期规则
    """
    try:
        rule = db.query(FundScheduleRule).filter(
            FundScheduleRule.fund_code == fund_code
        ).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到基金 {fund_code} 的档期规则"
            )

        db.delete(rule)
        db.commit()

        return APIResponse(
            success=True,
            message=f"成功删除基金 {fund_code} 的档期规则",
            data={"fund_code": fund_code}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除档期规则失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除档期规则失败: {str(e)}"
        )


@router.post("/calculate", response_model=APIResponse, summary="计算指定月份的开放日期")
async def calculate_dates(
    request: CalculateDatesRequest,
    db: Session = Depends(get_db)
):
    """
    根据档期规则计算指定月份的具体开放日期

    - **fund_code**: 基金代码
    - **year**: 年份
    - **month**: 月份
    """
    try:
        # 查询档期规则
        rule = db.query(FundScheduleRule).filter(
            FundScheduleRule.fund_code == request.fund_code
        ).first()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到基金 {request.fund_code} 的档期规则"
            )

        # 计算开放日期
        result = schedule_service.calculate_month_schedule(
            subscription_rule=rule.subscription_rule or "",
            redemption_rule=rule.redemption_rule or "",
            year=request.year,
            month=request.month
        )

        return APIResponse(
            success=True,
            message=f"成功计算 {request.year}年{request.month}月的开放日期",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算开放日期失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算开放日期失败: {str(e)}"
        )


@router.post("/calendar", response_model=APIResponse, summary="获取月历数据")
async def get_calendar(
    request: CalendarRequest,
    db: Session = Depends(get_db)
):
    """
    获取指定基金列表在指定月份的月历数据

    - **fund_codes**: 基金代码列表
    - **year**: 年份
    - **month**: 月份
    """
    try:
        # 查询选中基金的档期规则
        rules = db.query(
            FundScheduleRule,
            Fund.fund_name,
            Strategy.main_strategy,
            Strategy.sub_strategy
        ).join(
            Fund, FundScheduleRule.fund_code == Fund.fund_code
        ).outerjoin(
            Strategy, Fund.fund_code == Strategy.fund_code
        ).filter(
            FundScheduleRule.fund_code.in_(request.fund_codes)
        ).all()

        # 构建基金档期列表
        fund_schedules = []
        for rule, fund_name, main_strategy, sub_strategy in rules:
            fund_schedules.append({
                "fund_code": rule.fund_code,
                "fund_name": fund_name,
                "subscription_rule": rule.subscription_rule or "",
                "redemption_rule": rule.redemption_rule or "",
                "main_strategy": main_strategy or "",
                "sub_strategy": sub_strategy or ""
            })

        # 计算月历数据
        calendar_data = schedule_service.calculate_calendar_data(
            fund_schedules=fund_schedules,
            year=request.year,
            month=request.month
        )

        return APIResponse(
            success=True,
            message=f"成功获取 {request.year}年{request.month}月的月历数据",
            data=calendar_data
        )

    except Exception as e:
        logger.error(f"获取月历数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取月历数据失败: {str(e)}"
        )
