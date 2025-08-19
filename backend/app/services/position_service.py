"""
持仓分析服务
Position Analysis Service
"""

import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from ..models import Position, Client, Fund, Nav
from ..schemas.position import (
    PositionAnalysis, ClientPositionSummary, FundPositionSummary,
    TopHoldersResponse, PositionConcentrationAnalysis, PositionRiskMetrics
)

logger = logging.getLogger(__name__)


class PositionAnalysisService:
    """持仓分析服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_position_list(self,
                         group_id: Optional[str] = None,
                         fund_code: Optional[str] = None,
                         start_date: Optional[date] = None,
                         end_date: Optional[date] = None,
                         domestic_planner: Optional[str] = None,
                         page: int = 1,
                         page_size: int = 50) -> Tuple[List[Position], int]:
        """
        获取持仓列表（带分页和筛选）
        """
        try:
            # 构建查询
            query = self.db.query(Position).join(Client).join(Fund)
            
            # 应用筛选条件
            if group_id:
                query = query.filter(Position.group_id == group_id)
            if fund_code:
                query = query.filter(Position.fund_code == fund_code)
            if start_date:
                query = query.filter(Position.stock_date >= start_date)
            if end_date:
                query = query.filter(Position.stock_date <= end_date)
            if domestic_planner:
                query = query.filter(Client.domestic_planner.like(f"%{domestic_planner}%"))
            
            # 获取总数
            total = query.count()
            
            # 应用分页和排序
            positions = query.order_by(desc(Position.stock_date), Position.group_id)\
                            .offset((page - 1) * page_size)\
                            .limit(page_size)\
                            .all()
            
            return positions, total
            
        except Exception as e:
            logger.error(f"获取持仓列表失败: {str(e)}")
            raise
    
    def analyze_client_positions(self, group_id: str) -> ClientPositionSummary:
        """
        分析客户的全部持仓情况
        """
        try:
            # 获取客户信息
            client = self.db.query(Client).filter(Client.group_id == group_id).first()
            if not client:
                raise ValueError(f"客户 {group_id} 不存在")
            
            # 获取客户所有持仓
            positions = self.db.query(Position).filter(Position.group_id == group_id).all()
            
            if not positions:
                raise ValueError(f"客户 {group_id} 没有持仓记录")
            
            # 按基金分组计算
            fund_positions = []
            total_cost_with_fee = Decimal('0')
            total_cost_without_fee = Decimal('0')
            total_current_value = Decimal('0')
            total_unrealized_pnl = Decimal('0')
            
            # 按基金分组
            fund_groups = {}
            for pos in positions:
                if pos.fund_code not in fund_groups:
                    fund_groups[pos.fund_code] = []
                fund_groups[pos.fund_code].append(pos)
            
            for fund_code, fund_positions_list in fund_groups.items():
                fund_analysis = self._analyze_fund_position(group_id, fund_code, fund_positions_list)
                fund_positions.append(fund_analysis)
                
                total_cost_with_fee += fund_analysis.total_cost_with_fee or Decimal('0')
                total_cost_without_fee += fund_analysis.total_cost_without_fee or Decimal('0')
                
                if fund_analysis.current_market_value:
                    total_current_value += fund_analysis.current_market_value
                if fund_analysis.unrealized_pnl:
                    total_unrealized_pnl += fund_analysis.unrealized_pnl
            
            # 计算整体收益率
            overall_return_rate = None
            if total_cost_without_fee > 0:
                overall_return_rate = float(total_unrealized_pnl / total_cost_without_fee * 100)
            
            return ClientPositionSummary(
                group_id=group_id,
                client_name=client.obscured_name,
                domestic_planner=client.domestic_planner,
                total_funds=len(fund_groups),
                total_cost_with_fee=total_cost_with_fee,
                total_cost_without_fee=total_cost_without_fee,
                total_current_value=total_current_value if total_current_value > 0 else None,
                total_unrealized_pnl=total_unrealized_pnl if total_unrealized_pnl != 0 else None,
                overall_return_rate=round(overall_return_rate, 2) if overall_return_rate else None,
                fund_positions=fund_positions
            )
            
        except Exception as e:
            logger.error(f"分析客户持仓失败: {str(e)}")
            raise
    
    def _analyze_fund_position(self, group_id: str, fund_code: str, positions: List[Position]) -> PositionAnalysis:
        """
        分析单个基金的持仓情况
        """
        # 获取基金和客户信息
        fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
        client = self.db.query(Client).filter(Client.group_id == group_id).first()
        
        # 计算持仓汇总
        total_cost_with_fee = sum([pos.cost_with_fee or Decimal('0') for pos in positions])
        total_cost_without_fee = sum([pos.cost_without_fee or Decimal('0') for pos in positions])
        total_shares = sum([pos.shares or Decimal('0') for pos in positions])
        
        # 获取最新净值
        latest_nav_record = self.db.query(Nav).filter(Nav.fund_code == fund_code)\
                                           .order_by(desc(Nav.nav_date))\
                                           .first()
        
        # 计算市值和收益
        current_market_value = None
        unrealized_pnl = None
        return_rate = None
        
        if latest_nav_record and total_shares > 0:
            current_market_value = total_shares * latest_nav_record.unit_nav
            unrealized_pnl = current_market_value - total_cost_without_fee
            if total_cost_without_fee > 0:
                return_rate = float(unrealized_pnl / total_cost_without_fee * 100)
        
        # 计算费用
        total_fees = total_cost_with_fee - total_cost_without_fee if total_cost_with_fee and total_cost_without_fee else None
        fee_rate = None
        if total_fees and total_cost_without_fee > 0:
            fee_rate = float(total_fees / total_cost_without_fee * 100)
        
        return PositionAnalysis(
            group_id=group_id,
            fund_code=fund_code,
            client_name=client.obscured_name if client else None,
            fund_name=fund.fund_name if fund else None,
            total_cost_with_fee=total_cost_with_fee,
            total_cost_without_fee=total_cost_without_fee,
            total_shares=total_shares,
            position_records=len(positions),
            latest_nav=latest_nav_record.unit_nav if latest_nav_record else None,
            latest_nav_date=latest_nav_record.nav_date if latest_nav_record else None,
            current_market_value=current_market_value,
            unrealized_pnl=unrealized_pnl,
            return_rate=round(return_rate, 2) if return_rate else None,
            total_fees=total_fees,
            fee_rate=round(fee_rate, 2) if fee_rate else None
        )
    
    def analyze_fund_positions(self, fund_code: str) -> FundPositionSummary:
        """
        分析基金的所有持仓情况
        """
        try:
            # 获取基金信息
            fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
            if not fund:
                raise ValueError(f"基金 {fund_code} 不存在")
            
            # 获取基金所有持仓
            positions = self.db.query(Position).filter(Position.fund_code == fund_code).all()
            
            if not positions:
                raise ValueError(f"基金 {fund_code} 没有持仓记录")
            
            # 按客户分组
            client_groups = {}
            for pos in positions:
                if pos.group_id not in client_groups:
                    client_groups[pos.group_id] = []
                client_groups[pos.group_id].append(pos)
            
            # 分析每个客户的持仓
            client_positions = []
            total_cost_with_fee = Decimal('0')
            total_cost_without_fee = Decimal('0')
            total_shares = Decimal('0')
            
            for group_id, client_positions_list in client_groups.items():
                client_analysis = self._analyze_fund_position(group_id, fund_code, client_positions_list)
                client_positions.append(client_analysis)
                
                total_cost_with_fee += client_analysis.total_cost_with_fee or Decimal('0')
                total_cost_without_fee += client_analysis.total_cost_without_fee or Decimal('0')
                total_shares += client_analysis.total_shares or Decimal('0')
            
            # 获取最新净值
            latest_nav_record = self.db.query(Nav).filter(Nav.fund_code == fund_code)\
                                               .order_by(desc(Nav.nav_date))\
                                               .first()
            
            total_market_value = None
            if latest_nav_record and total_shares > 0:
                total_market_value = total_shares * latest_nav_record.unit_nav
            
            return FundPositionSummary(
                fund_code=fund_code,
                fund_name=fund.fund_name,
                total_clients=len(client_groups),
                total_cost_with_fee=total_cost_with_fee,
                total_cost_without_fee=total_cost_without_fee,
                total_shares=total_shares,
                latest_nav=latest_nav_record.unit_nav if latest_nav_record else None,
                latest_nav_date=latest_nav_record.nav_date if latest_nav_record else None,
                total_market_value=total_market_value,
                client_positions=client_positions
            )
            
        except Exception as e:
            logger.error(f"分析基金持仓失败: {str(e)}")
            raise
    
    def get_fund_top_holders(self, fund_code: str, top_n: int = 10) -> TopHoldersResponse:
        """
        获取基金前N大持有人
        """
        try:
            # 获取基金信息
            fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
            if not fund:
                raise ValueError(f"基金 {fund_code} 不存在")
            
            # 按客户汇总持仓
            client_positions = self.db.query(
                Position.group_id,
                Client.obscured_name,
                func.sum(Position.shares).label('total_shares'),
                func.sum(Position.cost_with_fee).label('total_cost')
            ).join(Client).filter(Position.fund_code == fund_code)\
             .group_by(Position.group_id, Client.obscured_name)\
             .order_by(desc('total_shares'))\
             .limit(top_n).all()
            
            # 获取最新净值
            latest_nav = self.db.query(Nav).filter(Nav.fund_code == fund_code)\
                                          .order_by(desc(Nav.nav_date))\
                                          .first()
            
            # 计算总市值
            total_shares = self.db.query(func.sum(Position.shares))\
                                 .filter(Position.fund_code == fund_code)\
                                 .scalar() or Decimal('0')
            
            total_market_value = None
            if latest_nav and total_shares > 0:
                total_market_value = total_shares * latest_nav.unit_nav
            
            # 构建前十大持有人列表
            top_holders = []
            for rank, (group_id, client_name, shares, cost) in enumerate(client_positions, 1):
                market_value = None
                percentage = None
                
                if latest_nav and shares:
                    market_value = shares * latest_nav.unit_nav
                    percentage = float(shares / total_shares * 100) if total_shares > 0 else 0
                
                top_holders.append({
                    "rank": rank,
                    "group_id": group_id,
                    "client_name": client_name,
                    "shares": float(shares) if shares else 0,
                    "market_value": float(market_value) if market_value else None,
                    "percentage": round(percentage, 2) if percentage else None
                })
            
            return TopHoldersResponse(
                fund_code=fund_code,
                fund_name=fund.fund_name,
                total_holders=self.db.query(Position.group_id).filter(Position.fund_code == fund_code).distinct().count(),
                total_market_value=total_market_value,
                top_holders=top_holders
            )
            
        except Exception as e:
            logger.error(f"获取基金前十大持有人失败: {str(e)}")
            raise
    
    def analyze_position_concentration(self, fund_code: str) -> PositionConcentrationAnalysis:
        """
        分析基金持仓集中度
        """
        try:
            # 获取基金信息
            fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
            if not fund:
                raise ValueError(f"基金 {fund_code} 不存在")
            
            # 按客户汇总持仓份额
            client_shares = self.db.query(
                Position.group_id,
                func.sum(Position.shares).label('total_shares')
            ).filter(Position.fund_code == fund_code)\
             .group_by(Position.group_id)\
             .all()
            
            if not client_shares:
                raise ValueError(f"基金 {fund_code} 没有持仓数据")
            
            # 转换为DataFrame进行分析
            df = pd.DataFrame([(group_id, float(shares)) for group_id, shares in client_shares],
                            columns=['group_id', 'shares'])
            
            df = df.sort_values('shares', ascending=False)
            total_shares = df['shares'].sum()
            df['percentage'] = df['shares'] / total_shares
            
            # 计算集中度指标
            # 赫芬达尔指数 (HHI)
            herfindahl_index = (df['percentage'] ** 2).sum()
            
            # 前5名和前10名集中度
            top5_concentration = df.head(5)['percentage'].sum() if len(df) >= 5 else df['percentage'].sum()
            top10_concentration = df.head(10)['percentage'].sum() if len(df) >= 10 else df['percentage'].sum()
            
            # 获取最新净值计算市值分布
            latest_nav = self.db.query(Nav).filter(Nav.fund_code == fund_code)\
                                          .order_by(desc(Nav.nav_date))\
                                          .first()
            
            if latest_nav:
                df['market_value'] = df['shares'] * float(latest_nav.unit_nav)
                
                # 按市值分类持有人
                large_holder_count = len(df[df['market_value'] > 1000000])  # 大于100万
                medium_holder_count = len(df[(df['market_value'] >= 100000) & (df['market_value'] <= 1000000)])  # 10-100万
                small_holder_count = len(df[df['market_value'] < 100000])  # 小于10万
            else:
                large_holder_count = medium_holder_count = small_holder_count = 0
            
            return PositionConcentrationAnalysis(
                fund_code=fund_code,
                fund_name=fund.fund_name,
                total_clients=len(df),
                herfindahl_index=round(herfindahl_index, 4),
                top5_concentration=round(top5_concentration * 100, 2),
                top10_concentration=round(top10_concentration * 100, 2),
                large_holder_count=large_holder_count,
                medium_holder_count=medium_holder_count,
                small_holder_count=small_holder_count
            )
            
        except Exception as e:
            logger.error(f"分析持仓集中度失败: {str(e)}")
            raise