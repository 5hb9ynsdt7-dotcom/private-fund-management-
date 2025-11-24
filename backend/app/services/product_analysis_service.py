"""
产品分析服务
Product Analysis Service
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from ..models import Nav, Fund

logger = logging.getLogger(__name__)


class ProductAnalysisService:
    """产品分析服务类"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_product(self, fund_code: str) -> Dict:
        """
        对指定产品进行全面分析

        Args:
            fund_code: 产品代码

        Returns:
            包含各项分析指标的字典
        """
        try:
            # 获取产品信息
            fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
            if not fund:
                raise ValueError(f"产品 {fund_code} 不存在")

            # 获取净值数据
            nav_records = self.db.query(Nav).filter(
                Nav.fund_code == fund_code
            ).order_by(Nav.nav_date).all()

            if not nav_records or len(nav_records) < 2:
                raise ValueError(f"产品 {fund_code} 净值数据不足")

            # 转换为DataFrame
            df = pd.DataFrame([
                {
                    'date': record.nav_date,
                    'nav': float(record.unit_nav),
                    'accumulated_nav': float(record.accum_nav) if record.accum_nav else None
                }
                for record in nav_records
            ])

            df = df.sort_values('date').reset_index(drop=True)

            # 计算各项指标
            basic_metrics = self._calculate_basic_metrics(df)
            risk_metrics = self._calculate_risk_metrics(df)
            holding_period_analysis = self._calculate_holding_period_analysis(df)
            monthly_analysis = self._calculate_monthly_analysis(df)
            nav_curve = self._prepare_nav_curve(df)

            return {
                'fund_code': fund_code,
                'fund_name': fund.fund_name,
                'data_start_date': df['date'].min().strftime('%Y-%m-%d'),
                'data_end_date': df['date'].max().strftime('%Y-%m-%d'),
                'total_days': len(df),
                'basic_metrics': basic_metrics,
                'risk_metrics': risk_metrics,
                'holding_period_analysis': holding_period_analysis,
                'monthly_stats': monthly_analysis['stats'],
                'monthly_returns': monthly_analysis['returns'],
                'nav_curve': nav_curve
            }

        except Exception as e:
            logger.error(f"产品分析失败 {fund_code}: {str(e)}")
            raise

    def _calculate_basic_metrics(self, df: pd.DataFrame) -> Dict:
        """计算基础指标"""
        try:
            # 计算日收益率
            df['daily_return'] = df['nav'].pct_change()

            # 累计收益率
            cumulative_return = (df['nav'].iloc[-1] / df['nav'].iloc[0] - 1) * 100

            # 年化收益率
            days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
            years = days / 365.0
            annualized_return = ((df['nav'].iloc[-1] / df['nav'].iloc[0]) ** (1 / years) - 1) * 100 if years > 0 else 0

            # 最大回撤
            df['cummax'] = df['nav'].cummax()
            df['drawdown'] = (df['nav'] / df['cummax'] - 1) * 100
            max_drawdown = df['drawdown'].min()

            # 波动率（年化）
            volatility = df['daily_return'].std() * np.sqrt(252) * 100 if len(df) > 1 else 0

            # 夏普比率（假设无风险利率为3%）
            risk_free_rate = 3.0
            excess_return = annualized_return - risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility != 0 else 0

            # 卡玛比率
            calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

            return {
                'cumulative_return': round(cumulative_return, 2),
                'annualized_return': round(annualized_return, 2),
                'max_drawdown': round(max_drawdown, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'calmar_ratio': round(calmar_ratio, 2)
            }
        except Exception as e:
            logger.error(f"计算基础指标失败: {str(e)}")
            raise

    def _calculate_risk_metrics(self, df: pd.DataFrame) -> Dict:
        """计算风险指标"""
        try:
            df['daily_return'] = df['nav'].pct_change()

            # 下行风险（年化）
            negative_returns = df['daily_return'][df['daily_return'] < 0]
            downside_deviation = negative_returns.std() * np.sqrt(252) * 100 if len(negative_returns) > 0 else 0

            # 索提诺比率
            risk_free_rate = 3.0
            days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
            years = days / 365.0
            annualized_return = ((df['nav'].iloc[-1] / df['nav'].iloc[0]) ** (1 / years) - 1) * 100 if years > 0 else 0
            excess_return = annualized_return - risk_free_rate
            sortino_ratio = excess_return / downside_deviation if downside_deviation != 0 else 0

            # 最大连续下跌天数
            df['is_loss'] = df['daily_return'] < 0
            consecutive_losses = []
            current_streak = 0
            for is_loss in df['is_loss']:
                if is_loss:
                    current_streak += 1
                else:
                    if current_streak > 0:
                        consecutive_losses.append(current_streak)
                    current_streak = 0
            if current_streak > 0:
                consecutive_losses.append(current_streak)
            max_consecutive_loss_days = max(consecutive_losses) if consecutive_losses else 0

            # VAR(95%)
            var_95 = np.percentile(df['daily_return'].dropna() * 100, 5)

            return {
                'downside_deviation': round(downside_deviation, 2),
                'sortino_ratio': round(sortino_ratio, 2),
                'max_consecutive_loss_days': int(max_consecutive_loss_days),
                'var_95': round(var_95, 2)
            }
        except Exception as e:
            logger.error(f"计算风险指标失败: {str(e)}")
            raise

    def _calculate_holding_period_analysis(self, df: pd.DataFrame) -> List[Dict]:
        """计算持有期分析"""
        try:
            periods = [
                ('6个月', 180),
                ('1年', 365),
                ('2年', 730)
            ]

            results = []

            for period_name, days in periods:
                returns = []

                # 遍历所有可能的买入点
                for i in range(len(df)):
                    # 找到持有期后的日期
                    target_date = df['date'].iloc[i] + timedelta(days=days)

                    # 找到最接近目标日期的记录
                    future_records = df[df['date'] >= target_date]
                    if len(future_records) > 0:
                        j = future_records.index[0]
                        # 计算收益率
                        holding_return = (df['nav'].iloc[j] / df['nav'].iloc[i] - 1) * 100
                        returns.append(holding_return)

                if returns:
                    profit_count = sum(1 for r in returns if r > 0)
                    profit_probability = (profit_count / len(returns)) * 100
                    avg_return = np.mean(returns)
                    max_return = max(returns)
                    min_return = min(returns)
                else:
                    profit_probability = 0
                    avg_return = 0
                    max_return = 0
                    min_return = 0

                results.append({
                    'period': period_name,
                    'sample_count': len(returns),
                    'profit_probability': round(profit_probability, 2),
                    'avg_return': round(avg_return, 2),
                    'max_return': round(max_return, 2),
                    'min_return': round(min_return, 2)
                })

            return results
        except Exception as e:
            logger.error(f"计算持有期分析失败: {str(e)}")
            raise

    def _calculate_monthly_analysis(self, df: pd.DataFrame) -> Dict:
        """计算月度分析"""
        try:
            # 确保date列是datetime类型
            df['date'] = pd.to_datetime(df['date'])

            # 按月分组
            df['year_month'] = df['date'].dt.to_period('M')
            monthly_data = df.groupby('year_month').agg({
                'nav': ['first', 'last']
            }).reset_index()

            monthly_data.columns = ['year_month', 'first_nav', 'last_nav']
            monthly_data['monthly_return'] = (monthly_data['last_nav'] / monthly_data['first_nav'] - 1) * 100

            # 月度胜率统计
            positive_months = (monthly_data['monthly_return'] > 0).sum()
            total_months = len(monthly_data)
            win_rate = (positive_months / total_months * 100) if total_months > 0 else 0

            stats = {
                'win_rate': round(win_rate, 2),
                'positive_months': int(positive_months),
                'negative_months': int(total_months - positive_months),
                'best_month': round(monthly_data['monthly_return'].max(), 2),
                'worst_month': round(monthly_data['monthly_return'].min(), 2),
                'avg_monthly_return': round(monthly_data['monthly_return'].mean(), 2)
            }

            # 月度收益列表
            returns = {
                'months': [str(ym) for ym in monthly_data['year_month']],
                'returns': [round(r, 2) for r in monthly_data['monthly_return']]
            }

            return {
                'stats': stats,
                'returns': returns
            }
        except Exception as e:
            logger.error(f"计算月度分析失败: {str(e)}")
            raise

    def _prepare_nav_curve(self, df: pd.DataFrame) -> Dict:
        """准备净值曲线数据"""
        try:
            # 计算累计最大值和回撤
            df['cummax'] = df['nav'].cummax()
            df['drawdown'] = (df['nav'] / df['cummax'] - 1) * 100

            return {
                'dates': [d.strftime('%Y-%m-%d') for d in df['date']],
                'values': [round(float(v), 4) for v in df['nav']],
                'drawdowns': [round(float(d), 2) for d in df['drawdown']]
            }
        except Exception as e:
            logger.error(f"准备净值曲线失败: {str(e)}")
            raise
