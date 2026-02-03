"""
阶段涨幅分析路由
Stage Performance Analysis Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
import logging
from pydantic import BaseModel

from ..database import get_db
from ..models import Fund, Nav, Strategy, Dividend
from ..schemas.common import APIResponse

logger = logging.getLogger(__name__)

# 阶段表现响应模型
class StagePerformanceResponse(BaseModel):
    fund_code: str
    fund_name: Optional[str] = None
    short_name: Optional[str] = None  # 产品简称
    major_strategy: Optional[str] = None
    sub_strategy: Optional[str] = None
    latest_nav_date: Optional[date] = None
    latest_nav: Optional[Decimal] = None
    previous_nav_date: Optional[date] = None
    previous_nav: Optional[Decimal] = None
    weekly_return: Optional[float] = None
    ytd_return: Optional[float] = None

class StagePerformanceListResponse(BaseModel):
    success: bool
    data: List[StagePerformanceResponse]
    total: int
    statistics: dict

router = APIRouter(
    prefix="/api/stage-performance",
    tags=["阶段涨幅分析"],
    responses={
        404: {"description": "资源未找到"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)

@router.get("/weekly", response_model=StagePerformanceListResponse, summary="获取产品近一周涨跌幅")
async def get_weekly_performance(
    search: Optional[str] = Query(None, description="搜索产品名称或代码"),
    major_strategy: Optional[str] = Query(None, description="大类策略筛选"),
    sub_strategy: Optional[str] = Query(None, description="细分策略筛选"),
    performance_filter: Optional[str] = Query(None, description="涨跌筛选: positive/negative/neutral"),
    days_limit: int = Query(7, description="最近数据限制天数", ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    获取产品近一周涨跌幅数据
    
    - **search**: 可选，按产品名称或代码搜索
    - **major_strategy**: 可选，按大类策略筛选
    - **sub_strategy**: 可选，按细分策略筛选
    - **performance_filter**: 可选，按涨跌情况筛选
    - **days_limit**: 数据时效限制，默认7天
    """
    try:
        # 计算日期范围
        today = date.today()
        cutoff_date = today - timedelta(days=days_limit)
        
        # 获取所有基金的最新净值记录
        latest_nav_subquery = db.query(
            Nav.fund_code,
            func.max(Nav.nav_date).label('latest_date')
        ).filter(
            Nav.nav_date >= cutoff_date
        ).group_by(Nav.fund_code).subquery()
        
        # 获取基金、策略和最新净值信息
        funds_query = db.query(
            Fund.fund_code,
            Fund.fund_name,
            Fund.short_name,
            Strategy.main_strategy,
            Strategy.sub_strategy,
            Nav.nav_date.label('latest_nav_date'),
            Nav.adjusted_accum_nav.label('latest_nav'),  # 使用复权累计净值
            Nav.accum_nav.label('latest_accum_nav')  # 备用：累计净值
        ).join(
            latest_nav_subquery,
            and_(
                Fund.fund_code == latest_nav_subquery.c.fund_code,
            )
        ).join(
            Nav,
            and_(
                Fund.fund_code == Nav.fund_code,
                Nav.nav_date == latest_nav_subquery.c.latest_date
            )
        ).outerjoin(
            Strategy,
            Fund.fund_code == Strategy.fund_code
        )
        
        # 应用筛选条件
        if search:
            funds_query = funds_query.filter(
                or_(
                    Fund.fund_name.like(f"%{search}%"),
                    Fund.fund_code.like(f"%{search}%")
                )
            )
        
        if major_strategy:
            funds_query = funds_query.filter(Strategy.main_strategy == major_strategy)
        
        if sub_strategy:
            funds_query = funds_query.filter(Strategy.sub_strategy == sub_strategy)
        
        funds_data = funds_query.all()
        
        # 为每个基金计算一周前的净值和涨跌幅
        performance_data = []
        
        # 计算今年年初日期
        year_start = date(today.year, 1, 1)
        
        for fund in funds_data:
            fund_code = fund.fund_code
            latest_date = fund.latest_nav_date

            # 确定使用哪种净值类型：优先使用adjusted_accum_nav，如果为空则使用accum_nav
            use_adjusted = fund.latest_nav is not None
            latest_nav = fund.latest_nav if use_adjusted else fund.latest_accum_nav

            # 计算一周前的日期（工作日逻辑）
            target_date = latest_date - timedelta(days=7)

            # 查找一周前最近的净值记录
            previous_nav_record = db.query(Nav).filter(
                and_(
                    Nav.fund_code == fund_code,
                    Nav.nav_date <= target_date
                )
            ).order_by(desc(Nav.nav_date)).first()

            # 查找基金的第一个净值记录（成立净值）
            first_nav_record = db.query(Nav).filter(
                Nav.fund_code == fund_code
            ).order_by(Nav.nav_date).first()

            # 判断是否为今年成立的基金
            is_founded_this_year = first_nav_record and first_nav_record.nav_date >= year_start

            if is_founded_this_year:
                # 今年成立的基金，使用成立净值作为基准
                ytd_nav_record = first_nav_record
            else:
                # 去年或更早成立的基金，查找上年最后一个交易日的净值记录
                ytd_nav_record = db.query(Nav).filter(
                    and_(
                        Nav.fund_code == fund_code,
                        Nav.nav_date < year_start
                    )
                ).order_by(desc(Nav.nav_date)).first()

            # 计算一周涨跌幅
            weekly_return = None
            previous_nav_date = None
            previous_nav = None

            if previous_nav_record and latest_nav:
                # 使用与最新净值相同的类型
                previous_nav_value = previous_nav_record.adjusted_accum_nav if use_adjusted else previous_nav_record.accum_nav

                if previous_nav_value:
                    previous_nav_date = previous_nav_record.nav_date
                    previous_nav = previous_nav_value

                    # 涨跌幅计算：(最新净值 - 前期净值) / 前期净值 * 100
                    weekly_return = float((latest_nav - previous_nav) / previous_nav * 100)

            # 计算今年以来涨跌幅
            ytd_return = None
            if ytd_nav_record and latest_nav:
                # 使用与最新净值相同的类型
                ytd_nav_value = ytd_nav_record.adjusted_accum_nav if use_adjusted else ytd_nav_record.accum_nav

                if ytd_nav_value:
                    if is_founded_this_year:
                        # 今年成立的基金：(最新净值 - 成立净值) / 成立净值 * 100
                        ytd_return = float((latest_nav - ytd_nav_value) / ytd_nav_value * 100)
                    else:
                        # 去年或更早成立的基金：(最新净值 - 上年最后一个净值) / 上年最后一个净值 * 100
                        ytd_return = float((latest_nav - ytd_nav_value) / ytd_nav_value * 100)
            
            # 应用涨跌筛选
            if performance_filter:
                if performance_filter == 'positive' and (weekly_return is None or weekly_return <= 0):
                    continue
                elif performance_filter == 'negative' and (weekly_return is None or weekly_return >= 0):
                    continue
                elif performance_filter == 'neutral' and (weekly_return is None or weekly_return != 0):
                    continue
            
            # 如果short_name为空或以"基金_"开头，使用fund_name
            display_name = fund.short_name
            if not display_name or display_name.startswith('基金_'):
                display_name = fund.fund_name

            performance_item = StagePerformanceResponse(
                fund_code=fund_code,
                fund_name=fund.fund_name,
                short_name=display_name,
                major_strategy=fund.main_strategy,
                sub_strategy=fund.sub_strategy,
                latest_nav_date=latest_date,
                latest_nav=latest_nav,
                previous_nav_date=previous_nav_date,
                previous_nav=previous_nav,
                weekly_return=weekly_return,
                ytd_return=ytd_return
            )
            
            performance_data.append(performance_item)
        
        # 计算统计信息
        total_products = len(performance_data)
        rising_products = len([p for p in performance_data if p.weekly_return and p.weekly_return > 0])
        falling_products = len([p for p in performance_data if p.weekly_return and p.weekly_return < 0])
        
        # 计算平均涨幅
        valid_returns = [p.weekly_return for p in performance_data if p.weekly_return is not None]
        avg_return = sum(valid_returns) / len(valid_returns) if valid_returns else 0
        
        statistics = {
            "total_products": total_products,
            "rising_products": rising_products,
            "falling_products": falling_products,
            "neutral_products": total_products - rising_products - falling_products,
            "avg_return": round(avg_return, 2)
        }
        
        # 三级排序（在Python中实现，与前端保持一致）
        def sort_key(item):
            # 第一级：大类策略排序
            strategy_order = {'成长配置': 0, '底仓配置': 1, '尾部对冲': 2}
            major_order = strategy_order.get(item.major_strategy, 999)
            
            # 第二级：细分策略排序
            sub_order = 999
            if item.major_strategy == '成长配置':
                sub_strategy_order = {'主观多头': 0, '量化多头': 1, '股票多头': 2, '股票多空': 3}
                sub_order = sub_strategy_order.get(item.sub_strategy, 999)
            elif item.major_strategy == '尾部对冲':
                sub_strategy_order = {'宏观策略': 0, 'CTA策略': 1}
                sub_order = sub_strategy_order.get(item.sub_strategy, 999)
            
            # 第三级：涨跌幅降序（大到小）
            weekly_return = item.weekly_return if item.weekly_return is not None else -999
            
            return (major_order, sub_order, -weekly_return)
        
        performance_data.sort(key=sort_key)
        
        logger.info(f"阶段涨幅分析完成: 共{total_products}个产品，涨{rising_products}跌{falling_products}")
        
        return StagePerformanceListResponse(
            success=True,
            data=performance_data,
            total=total_products,
            statistics=statistics
        )
        
    except Exception as e:
        logger.error(f"获取阶段涨幅数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取阶段涨幅数据失败: {str(e)}"
        )


@router.get("/period", summary="获取自定义期间涨跌幅")
async def get_period_performance(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    search: Optional[str] = Query(None, description="搜索产品名称或代码"),
    major_strategy: Optional[str] = Query(None, description="大类策略筛选"),
    sub_strategy: Optional[str] = Query(None, description="细分策略筛选"),
    db: Session = Depends(get_db)
):
    """
    获取自定义期间的产品涨跌幅数据
    
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **search**: 可选，按产品名称或代码搜索
    - **major_strategy**: 可选，按大类策略筛选
    - **sub_strategy**: 可选，按细分策略筛选
    """
    try:
        if start_date >= end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期必须早于结束日期"
            )
        
        # 获取基金和策略信息
        funds_query = db.query(
            Fund.fund_code,
            Fund.fund_name,
            Fund.short_name,
            Strategy.main_strategy,
            Strategy.sub_strategy
        ).outerjoin(Strategy, Fund.fund_code == Strategy.fund_code)
        
        # 应用筛选条件
        if search:
            funds_query = funds_query.filter(
                or_(
                    Fund.fund_name.like(f"%{search}%"),
                    Fund.fund_code.like(f"%{search}%")
                )
            )
        
        if major_strategy:
            funds_query = funds_query.filter(Strategy.main_strategy == major_strategy)
        
        if sub_strategy:
            funds_query = funds_query.filter(Strategy.sub_strategy == sub_strategy)
        
        funds = funds_query.all()
        
        performance_data = []
        
        for fund in funds:
            # 获取结束日期最近的净值
            end_nav_record = db.query(Nav).filter(
                and_(
                    Nav.fund_code == fund.fund_code,
                    Nav.nav_date <= end_date
                )
            ).order_by(desc(Nav.nav_date)).first()

            # 获取开始日期最近的净值
            start_nav_record = db.query(Nav).filter(
                and_(
                    Nav.fund_code == fund.fund_code,
                    Nav.nav_date >= start_date
                )
            ).order_by(Nav.nav_date).first()

            if end_nav_record and start_nav_record:
                # 确定使用哪种净值类型：优先使用adjusted_accum_nav，如果结束日期的为空则使用accum_nav
                use_adjusted = end_nav_record.adjusted_accum_nav is not None

                # 使用相同类型的净值
                end_nav_value = end_nav_record.adjusted_accum_nav if use_adjusted else end_nav_record.accum_nav
                start_nav_value = start_nav_record.adjusted_accum_nav if use_adjusted else start_nav_record.accum_nav

                if end_nav_value and start_nav_value:
                    period_return = float((end_nav_value - start_nav_value) / start_nav_value * 100)
                
                # 计算今年以来涨跌幅 - 使用最新净值和年初净值
                ytd_return = None
                today = date.today()
                year_start = date(today.year, 1, 1)

                # 查找基金的第一个净值记录（成立净值）
                first_nav_record = db.query(Nav).filter(
                    Nav.fund_code == fund.fund_code
                ).order_by(Nav.nav_date).first()

                # 判断是否为今年成立的基金
                is_founded_this_year = first_nav_record and first_nav_record.nav_date >= year_start

                if is_founded_this_year:
                    # 今年成立的基金，使用成立净值作为基准
                    ytd_nav_record = first_nav_record
                else:
                    # 去年或更早成立的基金，查找上年最后一个交易日的净值记录
                    ytd_nav_record = db.query(Nav).filter(
                        and_(
                            Nav.fund_code == fund.fund_code,
                            Nav.nav_date < year_start
                        )
                    ).order_by(desc(Nav.nav_date)).first()

                if ytd_nav_record and end_nav_record:
                    # 使用与结束日期净值相同的类型
                    ytd_nav_value = ytd_nav_record.adjusted_accum_nav if use_adjusted else ytd_nav_record.accum_nav
                    end_nav_value_for_ytd = end_nav_record.adjusted_accum_nav if use_adjusted else end_nav_record.accum_nav

                    if ytd_nav_value and end_nav_value_for_ytd:
                        if is_founded_this_year:
                            # 今年成立的基金：(最新净值 - 成立净值) / 成立净值 * 100
                            ytd_return = float((end_nav_value_for_ytd - ytd_nav_value) / ytd_nav_value * 100)
                        else:
                            # 去年或更早成立的基金：(最新净值 - 上年最后一个净值) / 上年最后一个净值 * 100
                            ytd_return = float((end_nav_value_for_ytd - ytd_nav_value) / ytd_nav_value * 100)

                # 如果short_name为空或以"基金_"开头，使用fund_name
                display_name = fund.short_name
                if not display_name or display_name.startswith('基金_'):
                    display_name = fund.fund_name

                performance_item = {
                    "fund_code": fund.fund_code,
                    "fund_name": fund.fund_name,
                    "short_name": display_name,
                    "major_strategy": fund.main_strategy,
                    "sub_strategy": fund.sub_strategy,
                    "start_nav_date": start_nav_record.nav_date,
                    "start_nav": start_nav_value,
                    "end_nav_date": end_nav_record.nav_date,
                    "end_nav": end_nav_value,
                    "period_return": period_return,
                    "ytd_return": ytd_return
                }

                performance_data.append(performance_item)
        
        return APIResponse(
            success=True,
            message=f"自定义期间({start_date}至{end_date})涨跌幅分析完成",
            data={
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "products": performance_data,
                "total": len(performance_data)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取自定义期间涨跌幅数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取自定义期间涨跌幅数据失败: {str(e)}"
        )