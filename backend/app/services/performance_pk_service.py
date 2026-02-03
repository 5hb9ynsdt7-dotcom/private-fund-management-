"""
业绩PK服务
Performance PK Service
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..models import Fund, Nav, BacktestPortfolio
from ..services.product_analysis_service import ProductAnalysisService

logger = logging.getLogger(__name__)


class PerformancePKService:
    """业绩PK服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.product_analysis_service = ProductAnalysisService(db)

    def compare_performance(
        self,
        objects: List[Dict[str, str]],
        time_range: str,
        custom_range: Optional[List[str]] = None,
        benchmark: Optional[str] = None,
        align_mode: str = 'common'
    ) -> Dict[str, Any]:
        """
        业绩对比分析

        Args:
            objects: 对比对象列表 [{'id': 'L01485', 'type': 'product'}, ...]
            time_range: 时间范围 ('1m', '3m', '6m', '1y', '3y', 'all', 'custom')
            custom_range: 自定义时间范围 ['2020-01-01', '2023-12-31']
            benchmark: 基准指数代码
            align_mode: 对齐方式 ('common', 'separate')

        Returns:
            对比分析结果
        """
        try:
            # 获取所有对象的净值数据
            nav_data_list = []
            full_nav_data_list = []  # 保存完整的原始数据
            object_names = []

            for obj in objects:
                obj_type = obj.get('type', 'product')
                obj_id = obj['id']

                # 处理不同类型的对象
                if obj_type in ['private', 'product']:
                    # 私募基金
                    nav_df = self._get_product_nav(obj_id)
                    fund = self.db.query(Fund).filter(Fund.fund_code == obj_id).first()
                    name = fund.short_name or fund.fund_name if fund else obj_id
                elif obj_type == 'public':
                    # 公募基金 - ID格式为 public_{fund_code}
                    fund_code = obj_id.replace('public_', '')
                    nav_df = self._get_public_fund_nav(fund_code)
                    from ..models_public_fund import PublicFund
                    fund = self.db.query(PublicFund).filter(PublicFund.fund_code == fund_code).first()
                    name = fund.fund_name if fund else fund_code
                elif obj_type == 'portfolio':
                    # 组合
                    nav_df = self._get_portfolio_nav(int(obj_id))
                    portfolio = self.db.query(BacktestPortfolio).filter(BacktestPortfolio.id == int(obj_id)).first()
                    name = portfolio.portfolio_name if portfolio else obj_id
                else:
                    logger.warning(f"未知的对象类型: {obj_type}")
                    continue

                if nav_df is not None and not nav_df.empty:
                    nav_data_list.append(nav_df)
                    full_nav_data_list.append(nav_df.copy())  # 保存完整数据的副本
                    object_names.append(name)
                else:
                    logger.warning(f"无法获取 {name} ({obj_id}) 的净值数据")

            if len(nav_data_list) < 2:
                raise ValueError("至少需要2个有效的对比对象")

            # 对齐时间范围
            aligned_data = self._align_time_range(
                nav_data_list,
                object_names,
                time_range,
                custom_range,
                align_mode
            )

            # 添加基准数据
            benchmark_full_df = None
            if benchmark:
                # 先获取完整的基准历史数据
                benchmark_full_df = self._get_benchmark_data(benchmark, None)
                if benchmark_full_df is not None and not benchmark_full_df.empty:
                    # 过滤到对比区间
                    start_date = pd.to_datetime(aligned_data['dates'][0])
                    end_date = pd.to_datetime(aligned_data['dates'][-1])
                    benchmark_df = benchmark_full_df[(benchmark_full_df['date'] >= start_date) & (benchmark_full_df['date'] <= end_date)].copy()

                    aligned_data['nav_data_list'].append(benchmark_df)
                    aligned_data['object_names'].append(self._get_benchmark_name(benchmark))
                    aligned_data['is_benchmark_list'].append(True)
                    # 保存基准的完整数据
                    full_nav_data_list.append(benchmark_full_df)

            # 计算各种指标
            metrics_list = []
            chart_data_list = []

            for i, (nav_df, name) in enumerate(zip(aligned_data['nav_data_list'], aligned_data['object_names'])):
                is_benchmark = aligned_data['is_benchmark_list'][i] if i < len(aligned_data['is_benchmark_list']) else False

                # 获取对应的完整数据
                full_df = full_nav_data_list[i] if i < len(full_nav_data_list) else nav_df

                # 计算指标 - 传入完整数据和基准标记
                metrics = self._calculate_metrics(nav_df, name, full_df, is_benchmark)
                metrics_list.append(metrics)

                # 准备图表数据 - 传递统一的dates数组
                chart_data = self._prepare_chart_data(nav_df, name, aligned_data['dates'], is_benchmark)
                chart_data_list.append(chart_data)

            return {
                'success': True,
                'dates': aligned_data['dates'],
                'chart_data': chart_data_list,
                'metrics': metrics_list,
                'time_range': time_range,
                'align_mode': align_mode
            }

        except Exception as e:
            logger.error(f"业绩对比分析失败: {str(e)}")
            raise

    def _get_product_nav(self, fund_code: str) -> Optional[pd.DataFrame]:
        """获取产品净值数据（使用累计净值，与产品分析页面保持一致）"""
        try:
            navs = (
                self.db.query(Nav)
                .filter(Nav.fund_code == fund_code)
                .order_by(Nav.nav_date)
                .all()
            )

            if not navs:
                return None

            # 使用累计净值，如果没有则使用单位净值
            df = pd.DataFrame([{
                'date': nav.nav_date,
                'nav': float(nav.accum_nav) if nav.accum_nav else float(nav.unit_nav)
            } for nav in navs])

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"获取产品净值失败 {fund_code}: {str(e)}")
            return None

    def _get_public_fund_nav(self, fund_code: str) -> Optional[pd.DataFrame]:
        """获取公募基金净值数据（使用累计净值，与产品分析页面保持一致）"""
        try:
            from ..models_public_fund import PublicFundNav

            navs = (
                self.db.query(PublicFundNav)
                .filter(PublicFundNav.fund_code == fund_code)
                .order_by(PublicFundNav.nav_date)
                .all()
            )

            if not navs:
                return None

            # 使用累计净值，如果没有则使用单位净值
            df = pd.DataFrame([{
                'date': nav.nav_date,
                'nav': float(nav.accum_nav) if nav.accum_nav else float(nav.unit_nav)
            } for nav in navs])

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"获取公募基金净值失败 {fund_code}: {str(e)}")
            return None

    def _get_portfolio_nav(self, portfolio_id: int) -> Optional[pd.DataFrame]:
        """获取组合净值数据 - 从保存的回测结果中读取"""
        try:
            portfolio = self.db.query(BacktestPortfolio).filter(BacktestPortfolio.id == portfolio_id).first()
            if not portfolio:
                logger.warning(f"组合 {portfolio_id} 不存在")
                return None

            if not portfolio.backtest_result:
                logger.warning(f"组合 {portfolio_id} 没有回测结果，请先保存组合或运行回测")
                return None

            # 解析回测结果
            import json
            result = json.loads(portfolio.backtest_result)

            if 'nav_curve' not in result:
                logger.warning(f"组合 {portfolio_id} 回测结果中没有净值曲线数据")
                return None

            nav_curve = result['nav_curve']
            df = pd.DataFrame({
                'date': pd.to_datetime(nav_curve['dates']),
                'nav': nav_curve['values']
            })

            return df

        except Exception as e:
            logger.error(f"获取组合净值失败 {portfolio_id}: {str(e)}")
            return None

    def _get_benchmark_data(self, benchmark_code: str, dates: List[str]) -> Optional[pd.DataFrame]:
        """获取基准数据（从东方财富API获取真实指数数据）"""
        try:
            import subprocess
            import urllib.parse
            import json

            # 基准代码映射
            benchmark_map = {
                '000300': '000300.SH',  # 沪深300
                '000905': '000905.SH',  # 中证500
                '000852': '000852.SH',  # 中证1000
                '000001': '000001.SH',  # 上证指数
                '399006': '399006.SZ',  # 创业板指
            }

            index_code = benchmark_map.get(benchmark_code)
            if not index_code:
                logger.warning(f"不支持的基准代码: {benchmark_code}")
                return None

            # 转换指数代码为东方财富格式
            secid_map = {
                '000300.SH': '1.000300',
                '000905.SH': '0.399905',
                '000852.SH': '1.000852',
                '000001.SH': '1.000001',
                '399006.SZ': '0.399006',
            }
            secid = secid_map.get(index_code, '0.399905')

            # 构建API请求
            base_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                "secid": secid,
                "fields1": "f1",
                "fields2": "f51,f53",  # f51=日期, f53=收盘价
                "klt": "101",  # 日K线
                "fqt": "1",  # 复权
                "end": "20500101",
                "lmt": "3000"
            }

            query_string = urllib.parse.urlencode(params)
            full_url = f"{base_url}?{query_string}"

            # 使用curl获取数据
            curl_cmd = [
                'curl', '-s',
                '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                '-H', 'Referer: https://quote.eastmoney.com/',
                '--compressed',
                full_url
            ]

            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                logger.error(f"获取基准数据失败: {result.stderr}")
                return None

            response_text = result.stdout
            if "(" in response_text and ")" in response_text:
                json_str = response_text[response_text.find("(") + 1:response_text.rfind(")")]
                data = json.loads(json_str)
            else:
                data = json.loads(response_text)

            if data.get("data") and data["data"].get("klines"):
                index_data = []
                for kline in data["data"]["klines"]:
                    fields = kline.split(",")
                    date_str = fields[0]
                    close_price = float(fields[1]) if len(fields) > 1 else 0

                    # 格式化日期
                    if len(date_str) == 8:
                        date_obj = datetime.strptime(date_str, "%Y%m%d")
                        date_str = date_obj.strftime("%Y-%m-%d")

                    index_data.append({
                        'date': date_str,
                        'value': close_price
                    })

                # 转换为DataFrame
                df = pd.DataFrame(index_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.rename(columns={'value': 'nav'})

                # 过滤到指定日期范围
                if dates:
                    start_date = pd.to_datetime(dates[0])
                    end_date = pd.to_datetime(dates[-1])
                    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

                logger.info(f"成功获取基准 {benchmark_code} 数据，共 {len(df)} 条")
                return df

            logger.warning(f"基准 {benchmark_code} API返回数据为空")
            return None

        except Exception as e:
            logger.error(f"获取基准数据失败 {benchmark_code}: {str(e)}")
            return None

    def _get_benchmark_name(self, benchmark_code: str) -> str:
        """获取基准名称"""
        benchmark_names = {
            '000300': '沪深300',
            '000905': '中证500',
            '000001': '上证指数',
            '399006': '创业板指',
            'HSI': '恒生指数',
            'MONEY_FUND': '货币基金'
        }
        return benchmark_names.get(benchmark_code, benchmark_code)

    def _align_time_range(
        self,
        nav_data_list: List[pd.DataFrame],
        object_names: List[str],
        time_range: str,
        custom_range: Optional[List[str]],
        align_mode: str
    ) -> Dict[str, Any]:
        """对齐时间范围"""

        # 根据时间范围和对齐模式确定过滤范围
        if time_range == 'custom' and custom_range:
            filter_start_date = pd.to_datetime(custom_range[0])
            filter_end_date = pd.to_datetime(custom_range[1])
        elif time_range != 'all':
            # 使用数据的最大日期作为结束日期
            data_end_date = max([df['date'].max() for df in nav_data_list])
            filter_end_date = data_end_date

            # 计算开始日期
            if time_range == '1m':
                filter_start_date = filter_end_date - timedelta(days=30)
            elif time_range == '3m':
                filter_start_date = filter_end_date - timedelta(days=90)
            elif time_range == '6m':
                filter_start_date = filter_end_date - timedelta(days=180)
            elif time_range == '1y':
                filter_start_date = filter_end_date - timedelta(days=365)
            elif time_range == '3y':
                filter_start_date = filter_end_date - timedelta(days=365 * 3)
            else:
                filter_start_date = None
                filter_end_date = None
        else:
            filter_start_date = None
            filter_end_date = None

        # 对齐模式处理
        aligned_nav_list = []

        if align_mode == 'common':
            # 共同区间模式：找出所有产品的共同区间
            if filter_start_date is not None and filter_end_date is not None:
                # 有时间范围限制
                common_start = max(filter_start_date, max([df['date'].min() for df in nav_data_list]))
                common_end = min(filter_end_date, min([df['date'].max() for df in nav_data_list]))
            else:
                # 成立以来：找共同区间
                common_start = max([df['date'].min() for df in nav_data_list])
                common_end = min([df['date'].max() for df in nav_data_list])

            # 验证共同区间是否有效
            if common_start > common_end:
                # 没有共同区间，记录详细信息
                date_ranges = []
                for i, df in enumerate(nav_data_list):
                    date_ranges.append(f"{object_names[i]}: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")

                error_msg = f"所选产品在指定时间范围内没有共同的数据区间。\n"
                error_msg += f"自定义时间范围: {filter_start_date.strftime('%Y-%m-%d') if filter_start_date else '不限'} 至 {filter_end_date.strftime('%Y-%m-%d') if filter_end_date else '不限'}\n"
                error_msg += "各产品数据范围:\n" + "\n".join(date_ranges)
                error_msg += "\n\n建议：请调整时间范围或切换到「按各自成立以来分别展示」模式。"

                logger.error(error_msg)
                raise ValueError(error_msg)

            # 所有产品都过滤到共同区间
            for df in nav_data_list:
                filtered_df = df[(df['date'] >= common_start) & (df['date'] <= common_end)].copy()
                if filtered_df.empty:
                    logger.warning(f"产品在共同区间 {common_start} 至 {common_end} 内无数据")
                aligned_nav_list.append(filtered_df)
        else:
            # 各自区间模式：每个产品保持自己的时间范围
            for df in nav_data_list:
                if filter_start_date is not None and filter_end_date is not None:
                    # 有时间范围限制，但每个产品只过滤自己有数据的部分
                    product_start = max(filter_start_date, df['date'].min())
                    product_end = min(filter_end_date, df['date'].max())
                    filtered_df = df[(df['date'] >= product_start) & (df['date'] <= product_end)].copy()
                else:
                    # 成立以来：保持完整数据
                    filtered_df = df.copy()
                aligned_nav_list.append(filtered_df)

        # 获取所有日期的并集
        all_dates = sorted(set().union(*[set(df['date']) for df in aligned_nav_list]))
        dates_str = [d.strftime('%Y-%m-%d') for d in all_dates]

        return {
            'nav_data_list': aligned_nav_list,
            'object_names': object_names,
            'dates': dates_str,
            'all_dates_set': set(all_dates),  # 保存日期集合供后续使用
            'is_benchmark_list': [False] * len(object_names)
        }

    def _calculate_metrics(self, nav_df: pd.DataFrame, name: str, full_nav_df: pd.DataFrame = None, is_benchmark: bool = False) -> Dict[str, Any]:
        """
        计算各项指标（与产品分析页面保持一致）
        nav_df: 过滤后的时间范围数据（用于计算区间收益）
        full_nav_df: 完整的净值数据（用于计算成立以来的指标）
        is_benchmark: 是否为基准数据（基准不显示回撤修复天数）
        """

        if nav_df.empty:
            return self._get_empty_metrics(name)

        # 如果没有传入完整数据，使用当前数据
        if full_nav_df is None or full_nav_df.empty:
            full_nav_df = nav_df

        # === 计算月度收益（用于波动率计算和月度表格）===
        full_nav_df = full_nav_df.copy()
        full_nav_df['date'] = pd.to_datetime(full_nav_df['date'])
        full_nav_df['year_month'] = full_nav_df['date'].dt.to_period('M')

        # 找到每个月最后一天的净值
        month_end_navs = []
        for year_month in full_nav_df['year_month'].unique():
            month_data = full_nav_df[full_nav_df['year_month'] == year_month]
            last_day = month_data.iloc[-1]
            month_end_navs.append({
                'year_month': year_month,
                'date': last_day['date'],
                'nav': last_day['nav']
            })

        month_end_df = pd.DataFrame(month_end_navs)
        month_end_df = month_end_df.sort_values('date').reset_index(drop=True)

        # 计算月度收益率列表
        monthly_returns_list = []
        for i in range(1, len(month_end_df)):
            prev_nav = month_end_df.iloc[i-1]['nav']
            curr_nav = month_end_df.iloc[i]['nav']
            monthly_return = (curr_nav / prev_nav - 1) * 100
            monthly_returns_list.append({
                'year_month': month_end_df.iloc[i]['year_month'],
                'monthly_return': monthly_return,
                'date': month_end_df.iloc[i]['date']
            })

        monthly_data = pd.DataFrame(monthly_returns_list)

        # === 收益类指标 ===
        # 区间收益
        period_return = ((nav_df['nav'].iloc[-1] / nav_df['nav'].iloc[0]) - 1) * 100 if len(nav_df) > 0 else 0

        # 计算不同时间范围的收益率（基于完整数据）
        end_date = full_nav_df['date'].max()
        start_date = full_nav_df['date'].min()

        # 计算产品成立的天数
        total_days = (end_date - start_date).days

        # 近1月
        date_1m = end_date - timedelta(days=30)
        df_1m = full_nav_df[full_nav_df['date'] >= date_1m]
        return_1m = ((df_1m['nav'].iloc[-1] / df_1m['nav'].iloc[0]) - 1) * 100 if len(df_1m) > 1 else None

        # 近3月
        date_3m = end_date - timedelta(days=90)
        df_3m = full_nav_df[full_nav_df['date'] >= date_3m]
        return_3m = ((df_3m['nav'].iloc[-1] / df_3m['nav'].iloc[0]) - 1) * 100 if len(df_3m) > 1 else None

        # 近1年
        date_1y = end_date - timedelta(days=365)
        df_1y = full_nav_df[full_nav_df['date'] >= date_1y]
        return_1y = ((df_1y['nav'].iloc[-1] / df_1y['nav'].iloc[0]) - 1) * 100 if len(df_1y) > 1 else None

        # 近3年（如果成立时间不足3年，返回None）
        if total_days >= 365 * 3:
            date_3y = end_date - timedelta(days=365*3)
            df_3y = full_nav_df[full_nav_df['date'] >= date_3y]
            return_3y = ((df_3y['nav'].iloc[-1] / df_3y['nav'].iloc[0]) - 1) * 100 if len(df_3y) > 1 else None
        else:
            return_3y = None

        # 近5年（如果成立时间不足5年，返回None）
        if total_days >= 365 * 5:
            date_5y = end_date - timedelta(days=365*5)
            df_5y = full_nav_df[full_nav_df['date'] >= date_5y]
            return_5y = ((df_5y['nav'].iloc[-1] / df_5y['nav'].iloc[0]) - 1) * 100 if len(df_5y) > 1 else None
        else:
            return_5y = None

        # 今年以来收益
        # 判断是否为今年成立的产品
        year_start = pd.Timestamp(end_date.year, 1, 1)
        is_founded_this_year = full_nav_df['date'].min() >= year_start

        if is_founded_this_year:
            # 今年成立的产品：使用成立净值作为基准
            ytd_df = full_nav_df.copy()
            ytd_return = ((ytd_df['nav'].iloc[-1] / ytd_df['nav'].iloc[0]) - 1) * 100 if len(ytd_df) > 0 else None
        else:
            # 去年或更早成立的产品：使用上年最后一个交易日的净值（12月31日或之前最近的交易日）
            last_year_df = full_nav_df[full_nav_df['date'] < year_start]
            if len(last_year_df) > 0:
                last_year_nav = last_year_df['nav'].iloc[-1]  # 上年最后一个交易日的净值
                current_nav = full_nav_df['nav'].iloc[-1]  # 最新净值
                ytd_return = ((current_nav / last_year_nav) - 1) * 100
            else:
                ytd_return = None

        # === 风险收益指标（成立以来）===
        # 累计收益
        cumulative_return = (full_nav_df['nav'].iloc[-1] / full_nav_df['nav'].iloc[0] - 1) * 100

        # 年化收益
        days = (full_nav_df['date'].iloc[-1] - full_nav_df['date'].iloc[0]).days
        years = days / 365.0
        # 确保 years 是标量值
        if isinstance(years, (list, tuple)) or hasattr(years, '__iter__') and not isinstance(years, (str, int, float)):
            logger.warning(f"{name} years 是列表类型: {type(years)}, 值: {years}")
            years = float(years[0]) if len(years) > 0 else 0.0
        else:
            years = float(years)

        logger.info(f"{name} 成立年限: {years}年, 类型: {type(years)}")
        annual_return = ((full_nav_df['nav'].iloc[-1] / full_nav_df['nav'].iloc[0]) ** (1 / years) - 1) * 100 if years > 0 else 0

        # 最大回撤
        cummax = full_nav_df['nav'].cummax()
        drawdown = (full_nav_df['nav'] / cummax - 1) * 100
        max_drawdown = abs(drawdown.min())

        # 年化波动率（使用月度收益率计算，与产品分析页面一致）
        if len(monthly_data) > 1:
            monthly_std = np.std(monthly_data['monthly_return'], ddof=1)  # 样本标准差
            volatility = monthly_std * np.sqrt(12)
        else:
            volatility = 0

        # 回撤修复时间（基准不显示回撤修复天数）
        if is_benchmark:
            logger.info(f"{name} 是基准数据，不计算回撤修复天数")
            recovery_days = None
        else:
            logger.info(f"{name} 是产品数据，计算回撤修复天数")
            max_dd_idx = drawdown.idxmin()
            recovery_df = full_nav_df[full_nav_df.index > max_dd_idx]
            recovery_nav = full_nav_df.loc[max_dd_idx, 'nav'] / (1 + drawdown.loc[max_dd_idx] / 100)
            recovery_idx = recovery_df[recovery_df['nav'] >= recovery_nav].index

            # 如果找到了恢复点，计算天数；否则标记为未修复
            if len(recovery_idx) > 0:
                recovery_days = (full_nav_df.loc[recovery_idx[0], 'date'] - full_nav_df.loc[max_dd_idx, 'date']).days
            else:
                # 使用 -1 表示未修复
                recovery_days = -1

        # 最近创新高时间
        latest_high_idx = cummax.idxmax()
        latest_high_date = full_nav_df.loc[latest_high_idx, 'date'].strftime('%Y-%m-%d') if latest_high_idx is not None else None

        # 夏普比率（假设无风险利率3%）
        risk_free_rate = 3.0
        excess_return = annual_return - risk_free_rate
        sharpe = excess_return / volatility if volatility > 0 else 0

        # 卡玛比率
        calmar = (annual_return / max_drawdown) if max_drawdown > 0 else 0

        # === 月度收益（按年份组织）===
        monthly_returns_by_year = {}

        # 如果monthly_data为空（产品刚成立，只有一个月的数据），跳过月度收益计算
        if len(monthly_data) > 0:
            monthly_data['year'] = monthly_data['year_month'].dt.year
            monthly_data['month'] = monthly_data['year_month'].dt.month

            # 构建月末净值字典
            month_end_nav_dict = {}
            for i, row in month_end_df.iterrows():
                ym = str(row['year_month'])
                month_end_nav_dict[ym] = row['nav']

            # 从月末净值中提取所有年份（包括只有1个月数据的年份）
            all_years_set = set()
            for i, row in month_end_df.iterrows():
                year = row['year_month'].year
                all_years_set.add(year)

            # 也包含有月度收益的年份
            all_years_set.update(monthly_data['year'].unique())

            year_list = sorted(all_years_set, reverse=True)

            for year in year_list:
                year_data = monthly_data[monthly_data['year'] == year]

                # 创建12个月的数据
                monthly_returns = {}
                for month in range(1, 13):
                    month_data = year_data[year_data['month'] == month]
                    if len(month_data) > 0:
                        monthly_returns[f'm{month}'] = round(month_data['monthly_return'].iloc[0], 2)
                    else:
                        monthly_returns[f'm{month}'] = None

                # 计算该年度的年度收益
                # 优先使用：本年最后一个月末净值 / 去年12月末净值 - 1
                prev_year_end_ym = f"{year-1}-12"

                # 找到该年最后一个有数据的月份
                year_months = year_data['year_month'].sort_values()
                if len(year_months) > 0:
                    last_month_ym = str(year_months.iloc[-1])

                    # 如果有去年12月的数据，使用去年12月作为基准
                    if prev_year_end_ym in month_end_nav_dict and last_month_ym in month_end_nav_dict:
                        prev_year_end_nav = month_end_nav_dict[prev_year_end_ym]
                        last_nav = month_end_nav_dict[last_month_ym]
                        year_total_return = round((last_nav / prev_year_end_nav - 1) * 100, 2)
                    else:
                        # 如果没有去年12月的数据（说明是成立第一年），使用该年第一个月作为起点
                        first_month_ym = str(year_months.iloc[0])
                        if first_month_ym in month_end_nav_dict and last_month_ym in month_end_nav_dict:
                            first_nav = month_end_nav_dict[first_month_ym]
                            last_nav = month_end_nav_dict[last_month_ym]
                            year_total_return = round((last_nav / first_nav - 1) * 100, 2)
                        else:
                            year_total_return = None
                else:
                    year_total_return = None

                # 计算月度胜率
                valid_months = [v for v in monthly_returns.values() if v is not None]
                if valid_months:
                    win_count = sum(1 for v in valid_months if v > 0)
                    win_rate = round(win_count / len(valid_months) * 100, 2)
                else:
                    win_rate = None

                monthly_returns['year_return'] = year_total_return
                monthly_returns['win_rate'] = win_rate

                monthly_returns_by_year[int(year)] = monthly_returns

        return {
            'name': name,
            # 收益类指标
            'periodReturn': round(period_return, 2) if period_return is not None else None,
            'return1m': round(return_1m, 2) if return_1m is not None else None,
            'return3m': round(return_3m, 2) if return_3m is not None else None,
            'return1y': round(return_1y, 2) if return_1y is not None else None,
            'return3y': round(return_3y, 2) if return_3y is not None else None,
            'return5y': round(return_5y, 2) if return_5y is not None else None,
            'ytdReturn': round(ytd_return, 2) if ytd_return is not None else None,
            # 风险收益指标
            'annualReturn': round(annual_return, 2),
            'volatility': round(volatility, 2),
            'maxDrawdown': round(max_drawdown, 2),
            'recoveryDays': int(recovery_days) if recovery_days is not None else -1,  # -1 表示未修复
            'latestHighDate': latest_high_date,
            'sharpe': round(sharpe, 2),
            'calmar': round(calmar, 2),
            'inceptionYears': round(years, 1) if years is not None and not isinstance(years, (list, tuple)) else None,  # 成立年限
            # 月度收益
            'monthlyReturns': monthly_returns_by_year
        }

    def _get_empty_metrics(self, name: str) -> Dict[str, Any]:
        """返回空指标"""
        return {
            'name': name,
            'periodReturn': None,
            'return1m': None,
            'return3m': None,
            'return1y': None,
            'return3y': None,
            'return5y': None,
            'ytdReturn': None,
            'annualReturn': None,
            'volatility': None,
            'maxDrawdown': None,
            'recoveryDays': -1,  # -1 表示未修复
            'latestHighDate': None,
            'sharpe': None,
            'calmar': None,
            'inceptionYears': None,  # 成立年限
            'monthlyReturns': {}
        }

    def _prepare_chart_data(
        self,
        nav_df: pd.DataFrame,
        name: str,
        all_dates: List[str],
        is_benchmark: bool = False
    ) -> Dict[str, Any]:
        """准备图表数据，确保数据数组与dates数组长度一致"""

        if nav_df.empty:
            return {
                'name': name,
                'return_data': [None] * len(all_dates),
                'drawdown_data': [None] * len(all_dates),
                'nav_data': [None] * len(all_dates),
                'is_benchmark': is_benchmark
            }

        # 创建日期到索引的映射
        nav_df = nav_df.copy()
        nav_df['date_str'] = nav_df['date'].dt.strftime('%Y-%m-%d')

        # 计算累计收益率
        cumulative_return = ((nav_df['nav'] / nav_df['nav'].iloc[0]) - 1) * 100
        nav_df['cumulative_return'] = cumulative_return

        # 计算回撤
        cummax = nav_df['nav'].cummax()
        drawdown = (nav_df['nav'] / cummax - 1) * 100
        nav_df['drawdown'] = drawdown

        # 创建日期到数据的映射
        date_to_return = dict(zip(nav_df['date_str'], nav_df['cumulative_return']))
        date_to_drawdown = dict(zip(nav_df['date_str'], nav_df['drawdown']))
        date_to_nav = dict(zip(nav_df['date_str'], nav_df['nav']))

        # 调试日志：输出净值范围
        logger.info(f"{name} 净值曲线数据范围: 最小={nav_df['nav'].min():.4f}, 最大={nav_df['nav'].max():.4f}, 起始={nav_df['nav'].iloc[0]:.4f}")

        # 生成与all_dates长度一致的数组，缺失日期填充None
        return_data = []
        drawdown_data = []
        nav_data = []

        for date_str in all_dates:
            if date_str in date_to_return:
                return_data.append(round(date_to_return[date_str], 2))
                drawdown_data.append(round(date_to_drawdown[date_str], 2))
                nav_data.append(round(date_to_nav[date_str], 4))
            else:
                return_data.append(None)
                drawdown_data.append(None)
                nav_data.append(None)

        return {
            'name': name,
            'return_data': return_data,
            'drawdown_data': drawdown_data,
            'nav_data': nav_data,
            'is_benchmark': is_benchmark
        }
