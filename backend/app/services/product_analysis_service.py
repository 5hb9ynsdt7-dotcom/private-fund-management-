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

            # 转换为DataFrame（使用累计净值以避免分红影响）
            df = pd.DataFrame([
                {
                    'date': record.nav_date,
                    'nav': float(record.accum_nav) if record.accum_nav else float(record.unit_nav),
                    'unit_nav': float(record.unit_nav)  # 保留单位净值用于显示
                }
                for record in nav_records
            ])

            df = df.sort_values('date').reset_index(drop=True)

            # 先计算月度分析，获取月度收益率用于波动率计算
            monthly_analysis = self._calculate_monthly_analysis(df)

            # 计算各项指标（将月度收益率传递给基础指标计算）
            basic_metrics = self._calculate_basic_metrics(df, monthly_analysis['returns']['returns'])
            risk_metrics = self._calculate_risk_metrics(df)
            holding_period_analysis = self._calculate_holding_period_analysis(df)
            nav_curve = self._prepare_nav_curve(df)
            peak_recovery = self._calculate_peak_recovery_time(df)
            max_drawdown_analysis = self._calculate_max_drawdown_recovery(df)

            # 获取策略信息
            main_strategy = fund.strategy.main_strategy if fund.strategy else '未分类'
            sub_strategy = fund.strategy.sub_strategy if fund.strategy else '未分类'

            return {
                'fund_code': fund_code,
                'fund_name': fund.fund_name,
                'short_name': fund.short_name or fund.fund_name,  # 简称，如果没有则使用全称
                'category_level1': main_strategy,
                'category_level2': sub_strategy,
                'data_start_date': df['date'].min().strftime('%Y-%m-%d'),
                'data_end_date': df['date'].max().strftime('%Y-%m-%d'),
                'total_days': len(df),
                'basic_metrics': basic_metrics,
                'risk_metrics': risk_metrics,
                'holding_period_analysis': holding_period_analysis,
                'monthly_stats': monthly_analysis['stats'],
                'monthly_returns': monthly_analysis,
                'nav_curve': nav_curve,
                'peak_recovery': peak_recovery,
                'max_drawdown_analysis': max_drawdown_analysis
            }

        except Exception as e:
            logger.error(f"产品分析失败 {fund_code}: {str(e)}")
            raise

    def _calculate_basic_metrics(self, df: pd.DataFrame, monthly_returns: list = None) -> Dict:
        """计算基础指标"""
        try:
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

            # 波动率（年化）- 使用月度收益率计算
            if monthly_returns and len(monthly_returns) > 1:
                # 月度收益率的标准差 * sqrt(12)
                monthly_std = np.std(monthly_returns, ddof=1)  # 使用样本标准差
                volatility = monthly_std * np.sqrt(12)
            else:
                volatility = 0

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
        """计算月度分析 - 使用月末最后一天的净值（和组合回测页面逻辑一致）"""
        try:
            # 确保date列是datetime类型
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            # 添加年月信息
            df['year_month'] = df['date'].dt.to_period('M')

            # 找到每个月最后一天的净值
            month_end_navs = []
            for year_month in df['year_month'].unique():
                month_data = df[df['year_month'] == year_month]
                # 取该月最后一天
                last_day = month_data.iloc[-1]
                month_end_navs.append({
                    'year_month': year_month,
                    'date': last_day['date'],
                    'nav': last_day['nav']
                })

            # 转换为DataFrame
            month_end_df = pd.DataFrame(month_end_navs)
            month_end_df = month_end_df.sort_values('date').reset_index(drop=True)

            # 计算月度收益（本月末净值 / 上月末净值 - 1）
            monthly_returns_list = []
            for i in range(1, len(month_end_df)):
                prev_nav = month_end_df.iloc[i-1]['nav']
                curr_nav = month_end_df.iloc[i]['nav']
                monthly_return = round((curr_nav / prev_nav - 1) * 100, 2)
                monthly_returns_list.append({
                    'year_month': month_end_df.iloc[i]['year_month'],
                    'monthly_return': monthly_return,
                    'date': month_end_df.iloc[i]['date']
                })

            monthly_data = pd.DataFrame(monthly_returns_list)

            # 月度胜率统计
            if len(monthly_data) > 0:
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
                    'returns': list(monthly_data['monthly_return'])
                }

                # 按年度组织的月度收益表
                monthly_data['year'] = monthly_data['year_month'].dt.year
                monthly_data['month'] = monthly_data['year_month'].dt.month

                yearly_monthly_table = []
                years = sorted(monthly_data['year'].unique(), reverse=True)  # 从近到远

                # 构建月末净值字典，方便查询
                month_end_nav_dict = {}
                for i, row in month_end_df.iterrows():
                    ym = str(row['year_month'])
                    month_end_nav_dict[ym] = row['nav']

                for year in years:
                    year_data = monthly_data[monthly_data['year'] == year]

                    # 创建12个月的数据，没有数据的月份为None
                    monthly_returns = {}
                    for month in range(1, 13):
                        month_data = year_data[year_data['month'] == month]
                        if len(month_data) > 0:
                            monthly_returns[f'month_{month}'] = month_data['monthly_return'].iloc[0]
                        else:
                            monthly_returns[f'month_{month}'] = None

                    # 计算该年度的胜率
                    year_returns = [monthly_returns[f'month_{i}'] for i in range(1, 13) if monthly_returns[f'month_{i}'] is not None]
                    if year_returns:
                        positive_count = sum(1 for r in year_returns if r > 0)
                        year_win_rate = round((positive_count / len(year_returns)) * 100, 2)
                    else:
                        year_win_rate = 0

                    # 计算年度总收益 = (本年末净值 - 去年12月末净值) / 去年12月末净值
                    # 和组合回测页面逻辑一致
                    year_end_ym = f"{year}-12"
                    prev_year_end_ym = f"{year-1}-12"

                    if year_end_ym in month_end_nav_dict and prev_year_end_ym in month_end_nav_dict:
                        year_end_nav = month_end_nav_dict[year_end_ym]
                        prev_year_end_nav = month_end_nav_dict[prev_year_end_ym]
                        year_total_return = round((year_end_nav / prev_year_end_nav - 1) * 100, 2)
                    else:
                        # 如果没有去年12月的数据，无法计算准确的年度收益
                        year_total_return = None

                    yearly_monthly_table.append({
                        'year': int(year),
                        **monthly_returns,
                        'year_return': year_total_return,
                        'win_rate': year_win_rate,
                        'total_months': len(year_returns)
                    })
            else:
                stats = {
                    'win_rate': 0,
                    'positive_months': 0,
                    'negative_months': 0,
                    'best_month': 0,
                    'worst_month': 0,
                    'avg_monthly_return': 0
                }
                returns = {'months': [], 'returns': []}
                yearly_monthly_table = []

            return {
                'stats': stats,
                'returns': returns,
                'yearly_table': yearly_monthly_table
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

    def _calculate_peak_recovery_time(self, df: pd.DataFrame) -> Dict:
        """
        计算从历史最高点回本所需时间

        Returns:
            包含最高点信息和回本时间的字典
        """
        try:
            # 找到历史最高净值点
            max_nav_idx = df['nav'].idxmax()
            max_nav = df['nav'].iloc[max_nav_idx]
            max_nav_date = df['date'].iloc[max_nav_idx]

            # 如果最高点是最后一天，说明当前在最高点
            if max_nav_idx == len(df) - 1:
                return {
                    'peak_nav': round(float(max_nav), 4),
                    'peak_date': max_nav_date.strftime('%Y-%m-%d'),
                    'recovery_days': 0,
                    'recovery_date': None,
                    'is_recovered': True,
                    'status': 'current_peak',
                    'current_drawdown_from_peak': 0.0
                }

            # 从最高点之后的数据中查找回本时间
            future_data = df.iloc[max_nav_idx + 1:]
            recovery_records = future_data[future_data['nav'] >= max_nav]

            if len(recovery_records) > 0:
                # 找到第一次回本的日期
                recovery_idx = recovery_records.index[0]
                recovery_date = df['date'].iloc[recovery_idx]
                recovery_days = (recovery_date - max_nav_date).days

                return {
                    'peak_nav': round(float(max_nav), 4),
                    'peak_date': max_nav_date.strftime('%Y-%m-%d'),
                    'recovery_days': int(recovery_days),
                    'recovery_date': recovery_date.strftime('%Y-%m-%d'),
                    'is_recovered': True,
                    'status': 'recovered',
                    'current_drawdown_from_peak': 0.0
                }
            else:
                # 还未回本
                current_nav = df['nav'].iloc[-1]
                current_drawdown = ((current_nav / max_nav - 1) * 100)
                days_since_peak = (df['date'].iloc[-1] - max_nav_date).days

                return {
                    'peak_nav': round(float(max_nav), 4),
                    'peak_date': max_nav_date.strftime('%Y-%m-%d'),
                    'recovery_days': None,
                    'recovery_date': None,
                    'is_recovered': False,
                    'status': 'not_recovered',
                    'current_drawdown_from_peak': round(float(current_drawdown), 2),
                    'days_since_peak': int(days_since_peak)
                }

        except Exception as e:
            logger.error(f"计算最高点回本时间失败: {str(e)}")
            raise

    def _calculate_max_drawdown_recovery(self, df: pd.DataFrame) -> Dict:
        """
        计算历史最大回撤发生时间和修复时长

        Returns:
            包含最大回撤详细信息的字典
        """
        try:
            # 计算累计最大值和回撤
            df['cummax'] = df['nav'].cummax()
            df['drawdown'] = (df['nav'] / df['cummax'] - 1) * 100

            # 找到最大回撤点（谷底）
            max_dd_idx = df['drawdown'].idxmin()
            max_dd_value = df['drawdown'].iloc[max_dd_idx]
            trough_date = df['date'].iloc[max_dd_idx]
            trough_nav = df['nav'].iloc[max_dd_idx]

            # 找到最大回撤对应的峰值点
            # 峰值是回撤点之前cummax等于trough对应cummax的最后一个点
            peak_nav = df['cummax'].iloc[max_dd_idx]
            peak_data = df[df['nav'] == peak_nav]

            # 找到谷底之前最后一个达到峰值的点
            peak_before_trough = peak_data[peak_data.index < max_dd_idx]
            if len(peak_before_trough) > 0:
                peak_idx = peak_before_trough.index[-1]
            else:
                # 如果找不到，可能峰值就在起点
                peak_idx = 0

            peak_date = df['date'].iloc[peak_idx]

            # 计算回撤持续时间（从峰值到谷底）
            drawdown_days = (trough_date - peak_date).days

            # 查找是否已经恢复
            # 恢复点 = 谷底之后净值再次达到或超过峰值净值
            future_data = df.iloc[max_dd_idx + 1:]
            recovery_records = future_data[future_data['nav'] >= peak_nav]

            if len(recovery_records) > 0:
                # 已恢复
                recovery_idx = recovery_records.index[0]
                recovery_date = df['date'].iloc[recovery_idx]
                recovery_days = (recovery_date - trough_date).days
                total_recovery_days = (recovery_date - peak_date).days

                return {
                    'max_drawdown': round(float(max_dd_value), 2),
                    'peak_date': peak_date.strftime('%Y-%m-%d'),
                    'peak_nav': round(float(peak_nav), 4),
                    'trough_date': trough_date.strftime('%Y-%m-%d'),
                    'trough_nav': round(float(trough_nav), 4),
                    'drawdown_days': int(drawdown_days),
                    'is_recovered': True,
                    'recovery_date': recovery_date.strftime('%Y-%m-%d'),
                    'recovery_days': int(recovery_days),
                    'total_recovery_days': int(total_recovery_days),
                    'status': 'recovered'
                }
            else:
                # 未恢复
                current_nav = df['nav'].iloc[-1]
                current_drawdown_from_peak = ((current_nav / peak_nav - 1) * 100)
                days_since_trough = (df['date'].iloc[-1] - trough_date).days
                days_since_peak = (df['date'].iloc[-1] - peak_date).days

                return {
                    'max_drawdown': round(float(max_dd_value), 2),
                    'peak_date': peak_date.strftime('%Y-%m-%d'),
                    'peak_nav': round(float(peak_nav), 4),
                    'trough_date': trough_date.strftime('%Y-%m-%d'),
                    'trough_nav': round(float(trough_nav), 4),
                    'drawdown_days': int(drawdown_days),
                    'is_recovered': False,
                    'recovery_date': None,
                    'recovery_days': None,
                    'total_recovery_days': None,
                    'days_since_trough': int(days_since_trough),
                    'days_since_peak': int(days_since_peak),
                    'current_nav': round(float(current_nav), 4),
                    'current_drawdown_from_peak': round(float(current_drawdown_from_peak), 2),
                    'status': 'not_recovered'
                }

        except Exception as e:
            logger.error(f"计算最大回撤修复时间失败: {str(e)}")
            raise
