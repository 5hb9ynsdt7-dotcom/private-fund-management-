"""
交易分析路由
Trade Analysis Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, extract
from typing import List, Optional
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
import logging

from ..database import get_db
from ..schemas.common import APIResponse, ErrorResponse
from ..models import Position, Client, Fund, Nav

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/trade",
    tags=["交易分析"],
    responses={
        404: {"model": ErrorResponse, "description": "资源未找到"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)


@router.get("/flow-analysis", response_model=APIResponse, summary="资金流向分析")
async def analyze_cash_flow(
    fund_code: Optional[str] = Query(None, description="基金代码筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    time_period: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly)$", description="时间周期"),
    db: Session = Depends(get_db)
):
    """
    分析资金流向情况
    
    - **fund_code**: 可选，指定基金分析
    - **start_date**: 开始日期
    - **end_date**: 结束日期  
    - **time_period**: 时间周期 (daily/weekly/monthly/quarterly)
    - **返回**: 资金流入流出统计
    """
    try:
        # 设置默认日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=365)
        
        # 构建查询
        query = db.query(Position)
        if fund_code:
            query = query.filter(Position.fund_code == fund_code)
        
        query = query.filter(
            and_(
                Position.stock_date >= start_date,
                Position.stock_date <= end_date
            )
        )
        
        positions = query.all()
        
        if not positions:
            return APIResponse(
                success=True,
                message="指定期间内没有交易数据",
                data={"cash_flow": [], "summary": {"total_inflow": 0, "total_outflow": 0, "net_flow": 0}}
            )
        
        # 转换为DataFrame进行分析
        df = pd.DataFrame([{
            'stock_date': pos.stock_date,
            'fund_code': pos.fund_code,
            'group_id': pos.group_id,
            'cost_with_fee': float(pos.cost_with_fee or 0),
            'cost_without_fee': float(pos.cost_without_fee or 0),
            'shares': float(pos.shares or 0)
        } for pos in positions])
        
        # 按时间周期分组
        if time_period == "daily":
            df['period'] = df['stock_date']
        elif time_period == "weekly":
            df['period'] = df['stock_date'].apply(lambda x: x - timedelta(days=x.weekday()))
        elif time_period == "monthly":
            df['period'] = df['stock_date'].apply(lambda x: x.replace(day=1))
        elif time_period == "quarterly":
            df['period'] = df['stock_date'].apply(lambda x: date(x.year, ((x.month-1)//3)*3+1, 1))
        
        # 计算资金流向（简化：正数为流入，负数为流出）
        flow_analysis = df.groupby('period').agg({
            'cost_with_fee': ['sum', 'count'],
            'shares': 'sum'
        }).round(2)
        
        flow_analysis.columns = ['total_cost', 'transaction_count', 'total_shares']
        flow_analysis = flow_analysis.reset_index()
        
        # 假设资金流向逻辑（实际应根据业务规则）
        # 这里简化为：cost > 0 为流入，cost < 0 为流出
        flow_data = []
        total_inflow = 0
        total_outflow = 0
        
        for _, row in flow_analysis.iterrows():
            period_str = row['period'].isoformat()
            cost = row['total_cost']
            
            if cost > 0:
                inflow = cost
                outflow = 0
                total_inflow += inflow
            else:
                inflow = 0
                outflow = abs(cost)
                total_outflow += outflow
            
            flow_data.append({
                "period": period_str,
                "inflow": inflow,
                "outflow": outflow,
                "net_flow": inflow - outflow,
                "transaction_count": int(row['transaction_count']),
                "total_shares": row['total_shares']
            })
        
        net_flow = total_inflow - total_outflow
        
        return APIResponse(
            success=True,
            message="资金流向分析完成",
            data={
                "cash_flow": flow_data,
                "summary": {
                    "total_inflow": round(total_inflow, 2),
                    "total_outflow": round(total_outflow, 2),
                    "net_flow": round(net_flow, 2),
                    "analysis_period": f"{start_date} 至 {end_date}",
                    "time_granularity": time_period
                }
            }
        )
        
    except Exception as e:
        logger.error(f"资金流向分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"资金流向分析失败: {str(e)}"
        )


@router.get("/client-activity", response_model=APIResponse, summary="客户交易活跃度分析")
async def analyze_client_activity(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    min_transactions: int = Query(1, ge=1, description="最小交易次数"),
    db: Session = Depends(get_db)
):
    """
    分析客户交易活跃度
    
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **min_transactions**: 最小交易次数筛选
    - **返回**: 客户活跃度排名和统计
    """
    try:
        # 设置默认日期范围
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=180)  # 默认6个月
        
        # 查询客户交易统计
        client_activity = db.query(
            Position.group_id,
            Client.obscured_name,
            Client.domestic_planner,
            func.count(Position.id).label('transaction_count'),
            func.count(func.distinct(Position.fund_code)).label('fund_count'),
            func.sum(Position.cost_with_fee).label('total_amount'),
            func.min(Position.stock_date).label('first_transaction'),
            func.max(Position.stock_date).label('last_transaction')
        ).join(Client).filter(
            and_(
                Position.stock_date >= start_date,
                Position.stock_date <= end_date
            )
        ).group_by(
            Position.group_id, Client.obscured_name, Client.domestic_planner
        ).having(
            func.count(Position.id) >= min_transactions
        ).order_by(
            desc('transaction_count')
        ).all()
        
        # 计算活跃度指标
        activity_data = []
        for stat in client_activity:
            # 计算交易频率（天/笔）
            days_span = (stat.last_transaction - stat.first_transaction).days + 1
            frequency = days_span / stat.transaction_count if stat.transaction_count > 0 else 0
            
            # 计算平均交易金额
            avg_amount = float(stat.total_amount or 0) / stat.transaction_count if stat.transaction_count > 0 else 0
            
            activity_data.append({
                "group_id": stat.group_id,
                "client_name": stat.obscured_name,
                "domestic_planner": stat.domestic_planner,
                "transaction_count": stat.transaction_count,
                "fund_count": stat.fund_count,
                "total_amount": float(stat.total_amount or 0),
                "avg_amount_per_transaction": round(avg_amount, 2),
                "transaction_frequency_days": round(frequency, 1),
                "first_transaction": stat.first_transaction.isoformat(),
                "last_transaction": stat.last_transaction.isoformat(),
                "active_days": days_span
            })
        
        # 计算统计摘要
        if activity_data:
            df = pd.DataFrame(activity_data)
            summary = {
                "total_active_clients": len(activity_data),
                "avg_transactions_per_client": round(df['transaction_count'].mean(), 1),
                "avg_amount_per_client": round(df['total_amount'].mean(), 2),
                "most_active_client": activity_data[0] if activity_data else None,
                "total_transactions": int(df['transaction_count'].sum()),
                "total_amount": round(df['total_amount'].sum(), 2)
            }
        else:
            summary = {
                "total_active_clients": 0,
                "avg_transactions_per_client": 0,
                "avg_amount_per_client": 0,
                "most_active_client": None,
                "total_transactions": 0,
                "total_amount": 0
            }
        
        return APIResponse(
            success=True,
            message="客户交易活跃度分析完成",
            data={
                "client_activity": activity_data,
                "summary": summary,
                "analysis_period": f"{start_date} 至 {end_date}"
            }
        )
        
    except Exception as e:
        logger.error(f"客户交易活跃度分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"客户交易活跃度分析失败: {str(e)}"
        )


@router.get("/fund-performance", response_model=APIResponse, summary="基金表现分析")
async def analyze_fund_performance(
    fund_code: Optional[str] = Query(None, description="基金代码"),
    benchmark_return: Optional[float] = Query(None, description="基准收益率"),
    period_days: int = Query(30, ge=1, le=365, description="分析期间天数"),
    db: Session = Depends(get_db)
):
    """
    分析基金表现和收益情况
    
    - **fund_code**: 可选，指定基金分析
    - **benchmark_return**: 可选，基准收益率
    - **period_days**: 分析期间天数
    - **返回**: 基金收益率、波动率、夏普比率等指标
    """
    try:
        # 获取分析的基金列表
        if fund_code:
            funds = [fund_code]
        else:
            fund_list = db.query(Fund.fund_code).all()
            funds = [f.fund_code for f in fund_list]
        
        performance_data = []
        
        for code in funds:
            # 获取基金信息
            fund = db.query(Fund).filter(Fund.fund_code == code).first()
            if not fund:
                continue
            
            # 获取净值数据
            end_date = date.today()
            start_date = end_date - timedelta(days=period_days)
            
            nav_records = db.query(Nav).filter(
                and_(
                    Nav.fund_code == code,
                    Nav.nav_date >= start_date,
                    Nav.nav_date <= end_date
                )
            ).order_by(Nav.nav_date).all()
            
            if len(nav_records) < 2:
                continue
            
            # 计算收益率
            nav_df = pd.DataFrame([{
                'nav_date': record.nav_date,
                'unit_nav': float(record.unit_nav)
            } for record in nav_records])
            
            nav_df = nav_df.sort_values('nav_date')
            nav_df['return'] = nav_df['unit_nav'].pct_change()
            
            # 计算性能指标
            latest_nav = nav_df['unit_nav'].iloc[-1]
            first_nav = nav_df['unit_nav'].iloc[0]
            total_return = (latest_nav / first_nav - 1) * 100
            
            daily_returns = nav_df['return'].dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100  # 年化波动率
            
            # 夏普比率（假设无风险利率为3%）
            risk_free_rate = 0.03
            annualized_return = total_return * (365 / period_days) / 100
            sharpe_ratio = (annualized_return - risk_free_rate) / (volatility / 100) if volatility > 0 else 0
            
            # 最大回撤
            nav_df['cumulative'] = (1 + nav_df['return'].fillna(0)).cumprod()
            nav_df['peak'] = nav_df['cumulative'].cummax()
            nav_df['drawdown'] = (nav_df['cumulative'] / nav_df['peak'] - 1) * 100
            max_drawdown = nav_df['drawdown'].min()
            
            # 获取持仓统计
            position_stats = db.query(
                func.count(func.distinct(Position.group_id)).label('client_count'),
                func.sum(Position.cost_with_fee).label('total_aum'),
                func.sum(Position.shares).label('total_shares')
            ).filter(Position.fund_code == code).first()
            
            current_aum = None
            if position_stats.total_shares and latest_nav:
                current_aum = float(position_stats.total_shares) * latest_nav
            
            performance_data.append({
                "fund_code": code,
                "fund_name": fund.fund_name,
                "latest_nav": latest_nav,
                "total_return_pct": round(total_return, 2),
                "annualized_return_pct": round(annualized_return * 100, 2),
                "volatility_pct": round(volatility, 2),
                "sharpe_ratio": round(sharpe_ratio, 3),
                "max_drawdown_pct": round(max_drawdown, 2),
                "client_count": position_stats.client_count or 0,
                "total_aum": float(position_stats.total_aum or 0),
                "current_market_value": round(current_aum, 2) if current_aum else None,
                "nav_records_count": len(nav_records),
                "analysis_period_days": period_days
            })
        
        # 排序（按总收益率降序）
        performance_data.sort(key=lambda x: x['total_return_pct'], reverse=True)
        
        return APIResponse(
            success=True,
            message="基金表现分析完成",
            data={
                "fund_performance": performance_data,
                "analysis_summary": {
                    "total_funds_analyzed": len(performance_data),
                    "period_days": period_days,
                    "best_performer": performance_data[0] if performance_data else None,
                    "avg_return": round(sum([f['total_return_pct'] for f in performance_data]) / len(performance_data), 2) if performance_data else 0
                }
            }
        )
        
    except Exception as e:
        logger.error(f"基金表现分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"基金表现分析失败: {str(e)}"
        )


@router.get("/seasonal-analysis", response_model=APIResponse, summary="季节性交易分析")
async def analyze_seasonal_patterns(
    fund_code: Optional[str] = Query(None, description="基金代码"),
    year: Optional[int] = Query(None, ge=2020, le=2030, description="指定年份"),
    db: Session = Depends(get_db)
):
    """
    分析交易的季节性模式
    
    - **fund_code**: 可选，指定基金
    - **year**: 可选，指定年份
    - **返回**: 按月份、季度的交易模式分析
    """
    try:
        # 构建查询
        query = db.query(Position)
        
        if fund_code:
            query = query.filter(Position.fund_code == fund_code)
        
        if year:
            query = query.filter(extract('year', Position.stock_date) == year)
        
        positions = query.all()
        
        if not positions:
            return APIResponse(
                success=True,
                message="没有找到符合条件的交易数据",
                data={"seasonal_patterns": {}}
            )
        
        # 转换为DataFrame
        df = pd.DataFrame([{
            'stock_date': pos.stock_date,
            'month': pos.stock_date.month,
            'quarter': (pos.stock_date.month - 1) // 3 + 1,
            'year': pos.stock_date.year,
            'cost_with_fee': float(pos.cost_with_fee or 0),
            'shares': float(pos.shares or 0)
        } for pos in positions])
        
        # 按月份统计
        monthly_stats = df.groupby('month').agg({
            'cost_with_fee': ['sum', 'mean', 'count'],
            'shares': 'sum'
        }).round(2)
        
        monthly_stats.columns = ['total_amount', 'avg_amount', 'transaction_count', 'total_shares']
        monthly_stats = monthly_stats.reset_index()
        
        monthly_data = [
            {
                "month": int(row['month']),
                "month_name": ["", "一月", "二月", "三月", "四月", "五月", "六月", 
                              "七月", "八月", "九月", "十月", "十一月", "十二月"][int(row['month'])],
                "total_amount": row['total_amount'],
                "avg_amount": row['avg_amount'],
                "transaction_count": int(row['transaction_count']),
                "total_shares": row['total_shares']
            }
            for _, row in monthly_stats.iterrows()
        ]
        
        # 按季度统计
        quarterly_stats = df.groupby('quarter').agg({
            'cost_with_fee': ['sum', 'mean', 'count'],
            'shares': 'sum'
        }).round(2)
        
        quarterly_stats.columns = ['total_amount', 'avg_amount', 'transaction_count', 'total_shares']
        quarterly_stats = quarterly_stats.reset_index()
        
        quarterly_data = [
            {
                "quarter": int(row['quarter']),
                "quarter_name": f"第{int(row['quarter'])}季度",
                "total_amount": row['total_amount'],
                "avg_amount": row['avg_amount'],
                "transaction_count": int(row['transaction_count']),
                "total_shares": row['total_shares']
            }
            for _, row in quarterly_stats.iterrows()
        ]
        
        # 按年份统计（如果有多年数据）
        yearly_stats = df.groupby('year').agg({
            'cost_with_fee': ['sum', 'mean', 'count'],
            'shares': 'sum'
        }).round(2)
        
        yearly_stats.columns = ['total_amount', 'avg_amount', 'transaction_count', 'total_shares']
        yearly_stats = yearly_stats.reset_index()
        
        yearly_data = [
            {
                "year": int(row['year']),
                "total_amount": row['total_amount'],
                "avg_amount": row['avg_amount'],
                "transaction_count": int(row['transaction_count']),
                "total_shares": row['total_shares']
            }
            for _, row in yearly_stats.iterrows()
        ]
        
        return APIResponse(
            success=True,
            message="季节性交易分析完成",
            data={
                "seasonal_patterns": {
                    "monthly": monthly_data,
                    "quarterly": quarterly_data,
                    "yearly": yearly_data
                },
                "summary": {
                    "peak_month": monthly_data[0]["month_name"] if monthly_data else None,
                    "peak_quarter": quarterly_data[0]["quarter_name"] if quarterly_data else None,
                    "total_years_analyzed": len(yearly_data),
                    "analysis_scope": f"基金: {fund_code or '全部'}, 年份: {year or '全部'}"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"季节性交易分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"季节性交易分析失败: {str(e)}"
        )