"""
组合回测服务
Portfolio Backtest Service
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import numpy as np
import pandas as pd

from ..models import Nav, Fund
from .portfolio_nav_service import PortfolioNavService

logger = logging.getLogger(__name__)


class PortfolioBacktestService:
    """组合回测服务类"""

    def __init__(self):
        self.risk_free_rate = 0.02  # 无风险利率，默认2%

    async def run_backtest(
        self,
        db: Session,
        portfolio: List[Any],
        initial_capital: float,
        start_date: str,
        end_date: str,
        benchmark: str,
        benchmark_product: str,
        rebalance_frequency: str,
        reinvest_dividend: bool,
        consider_fees: bool,
        weight_mode: str,
        portfolio_id: Optional[int] = None,
        portfolio_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行组合回测

        Args:
            db: 数据库会话
            portfolio: 组合列表
            initial_capital: 初始资金（万元）
            start_date: 开始日期
            end_date: 结束日期
            benchmark: 基准指数代码
            benchmark_product: 基准产品代码
            rebalance_frequency: 调仓频率
            reinvest_dividend: 是否分红再投资
            consider_fees: 是否考虑费用
            weight_mode: 配置模式

        Returns:
            回测结果字典
        """
        logger.info(f"开始组合回测: {start_date} 到 {end_date}")

        # 1. 获取所有产品的净值数据
        nav_data = await self._fetch_nav_data(db, portfolio, start_date, end_date)

        if not nav_data:
            raise ValueError("未找到有效的净值数据")

        # 2. 如果回测从某年1月1日开始，获取上一年12月的净值用于计算1月收益率
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if start_dt.month == 1 and start_dt.day == 1:
            # 计算上一年12月的日期范围
            prev_year = start_dt.year - 1
            prev_dec_start = f"{prev_year}-12-01"
            prev_dec_end = f"{prev_year}-12-31"

            logger.info(f"回测从1月1日开始，获取上一年12月净值: {prev_dec_start} 到 {prev_dec_end}")

            # 获取上一年12月的净值数据
            for item in portfolio:
                fund_code = item.fund_code

                # 查询上一年12月的净值，按日期降序，取最后一个交易日
                prev_navs = db.query(Nav).filter(
                    and_(
                        Nav.fund_code == fund_code,
                        Nav.nav_date >= prev_dec_start,
                        Nav.nav_date <= prev_dec_end
                    )
                ).order_by(Nav.nav_date.desc()).limit(1).all()

                if prev_navs and fund_code in nav_data:
                    # 将上一年12月的最后一个净值添加到nav_data中
                    prev_nav = prev_navs[0]
                    prev_date = prev_nav.nav_date.strftime('%Y-%m-%d')
                    nav_data[fund_code][prev_date] = float(prev_nav.accum_nav)
                    logger.info(f"产品 {fund_code} 补充上一年12月净值: {prev_date} = {prev_nav.accum_nav}")

        # 3. 计算初始权重
        if weight_mode == "weight":
            weights = {item.fund_code: item.weight for item in portfolio}
        else:
            # 按金额配置，计算权重
            total_amount = sum(item.amount for item in portfolio)
            weights = {item.fund_code: item.amount / total_amount for item in portfolio}

        # 4. 构建组合净值序列
        portfolio_nav_series = self._calculate_portfolio_nav(
            nav_data, weights, initial_capital, rebalance_frequency
        )

        if len(portfolio_nav_series) == 0:
            raise ValueError("无法计算组合净值")

        # 5. 计算性能指标
        metrics = self._calculate_metrics(portfolio_nav_series)

        # 6. 计算回撤曲线
        drawdown_curve = self._calculate_drawdown_curve(portfolio_nav_series)

        # 6.5. 计算最大回撤详细信息
        max_drawdown_info = self._calculate_max_drawdown_info(portfolio_nav_series)

        # 7. 计算年度收益
        yearly_returns = self._calculate_yearly_returns(portfolio_nav_series, start_date)

        # 8. 计算持仓信息
        position_info = self._calculate_position_info(portfolio_nav_series, initial_capital)

        # 9. 计算月度区间收益
        monthly_returns = self._calculate_monthly_returns(portfolio_nav_series, start_date)

        # 10. 计算季度收益贡献
        quarterly_contributions = self._calculate_quarterly_contributions(
            nav_data, weights, initial_capital, start_date
        )

        # 10.5. 获取基准数据
        benchmark_nav_curve = None
        benchmark_drawdown_curve = None
        if benchmark:
            # 基准为指数
            portfolio_dates = list(portfolio_nav_series.keys())
            benchmark_nav_curve, benchmark_drawdown_curve = self._get_benchmark_curves(
                benchmark, start_date, end_date, portfolio_dates
            )
        elif benchmark_product:
            # 基准为产品
            portfolio_dates = list(portfolio_nav_series.keys())
            benchmark_nav_curve, benchmark_drawdown_curve = await self._get_product_benchmark_curves(
                db, benchmark_product, start_date, end_date, portfolio_dates
            )

        # 10.6. 分析创新高事件
        new_high_analysis = self._analyze_new_highs(
            portfolio_nav_series,
            benchmark_nav_curve if benchmark else None
        )

        # 11. 准备返回数据
        result = {
            "metrics": metrics,
            "positionInfo": position_info,
            "navCurve": [
                {"date": date, "nav": nav}
                for date, nav in portfolio_nav_series.items()
            ],
            "drawdownCurve": drawdown_curve,
            "maxDrawdownInfo": max_drawdown_info,
            "yearlyReturns": yearly_returns,
            "monthlyReturns": monthly_returns,
            "quarterlyContributions": quarterly_contributions,
            "benchmarkNavCurve": benchmark_nav_curve,
            "benchmarkDrawdownCurve": benchmark_drawdown_curve,
            "newHighAnalysis": new_high_analysis,
            "backtestInfo": {
                "startDate": start_date,
                "endDate": end_date,
                "initialCapital": initial_capital,
                "rebalanceFrequency": rebalance_frequency,
                "portfolioCount": len(portfolio)
            }
        }

        # 12. 如果提供了 portfolio_id，保存周度净值到数据库
        if portfolio_id and portfolio_name:
            try:
                weekly_navs = self._extract_weekly_nav(portfolio_nav_series)
                if weekly_navs:
                    nav_service = PortfolioNavService()
                    saved_count = nav_service.save_portfolio_nav_batch(
                        db=db,
                        portfolio_type='backtest',
                        portfolio_id=portfolio_id,
                        portfolio_name=portfolio_name,
                        nav_data=weekly_navs
                    )
                    logger.info(f"回测组合 {portfolio_name} (ID: {portfolio_id}) 保存了 {saved_count} 条周度净值")
            except Exception as e:
                logger.error(f"保存回测组合净值失败: {str(e)}", exc_info=True)
                # 不影响回测结果返回

        return result

    async def _fetch_nav_data(
        self,
        db: Session,
        portfolio: List[Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Dict[str, float]]:
        """
        获取所有产品的净值数据

        Returns:
            {
                'fund_code': {
                    'date': nav_value,
                    ...
                },
                ...
            }
        """
        nav_data = {}

        for item in portfolio:
            fund_code = item.fund_code

            # 查询该产品的净值数据
            navs = db.query(Nav).filter(
                and_(
                    Nav.fund_code == fund_code,
                    Nav.nav_date >= start_date,
                    Nav.nav_date <= end_date
                )
            ).order_by(Nav.nav_date).all()

            if not navs:
                logger.warning(f"产品 {fund_code} 在指定时间范围内没有净值数据")
                continue

            # 转换为字典
            nav_dict = {
                nav.nav_date.strftime('%Y-%m-%d'): float(nav.accum_nav)  # 使用累计净值
                for nav in navs
            }

            nav_data[fund_code] = nav_dict

        return nav_data

    def _calculate_portfolio_nav(
        self,
        nav_data: Dict[str, Dict[str, float]],
        weights: Dict[str, float],
        initial_capital: float,
        rebalance_frequency: str
    ) -> Dict[str, float]:
        """
        计算组合净值序列

        Returns:
            {'date': nav_value, ...}
        """
        # 获取所有日期的并集
        all_dates = set()
        for fund_navs in nav_data.values():
            all_dates.update(fund_navs.keys())

        all_dates = sorted(list(all_dates))

        if not all_dates:
            return {}

        # 初始化组合净值为1.0
        portfolio_nav_series = {}
        portfolio_nav = 1.0

        # 记录每个产品的前一日净值
        prev_navs = {}

        for date in all_dates:
            # 计算当日组合收益率
            daily_return = 0.0

            for fund_code, weight in weights.items():
                if fund_code not in nav_data:
                    continue

                fund_navs = nav_data[fund_code]

                # 获取当日净值
                current_nav = fund_navs.get(date)

                if current_nav is None:
                    # 如果当日没有净值，使用前一日净值
                    current_nav = prev_navs.get(fund_code)

                if current_nav is None:
                    # 如果还是没有，跳过
                    continue

                # 获取前一日净值
                prev_nav = prev_navs.get(fund_code)

                if prev_nav is not None:
                    # 计算单日收益率
                    fund_return = (current_nav - prev_nav) / prev_nav
                    daily_return += weight * fund_return

                # 更新前一日净值
                prev_navs[fund_code] = current_nav

            # 更新组合净值
            portfolio_nav = portfolio_nav * (1 + daily_return)
            portfolio_nav_series[date] = portfolio_nav

        return portfolio_nav_series

    def _calculate_metrics(self, nav_series: Dict[str, float]) -> Dict[str, float]:
        """
        计算性能指标
        """
        if not nav_series or len(nav_series) < 2:
            return self._get_empty_metrics()

        # 转换为列表
        dates = list(nav_series.keys())
        navs = list(nav_series.values())

        # 只计算实际有变化的日期的收益率（过滤掉净值没有变化的日期）
        returns = []
        actual_trading_days = 0

        for i in range(1, len(navs)):
            if navs[i] != navs[i-1]:  # 只有净值变化的日期才计算收益率
                ret = (navs[i] - navs[i-1]) / navs[i-1]
                returns.append(ret)
                actual_trading_days += 1

        if not returns or len(returns) < 2:
            return self._get_empty_metrics()

        returns = np.array(returns)

        # 基本指标
        total_return = (navs[-1] - navs[0]) / navs[0]

        # 计算时间跨度和年化系数
        start_date = datetime.strptime(dates[0], '%Y-%m-%d')
        end_date = datetime.strptime(dates[-1], '%Y-%m-%d')
        days = (end_date - start_date).days
        years = days / 365.0

        # 年化收益率
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # 年化波动率 - 使用样本标准差，并根据实际交易日数年化
        # 计算年化系数：假设一年有252个交易日，按实际交易日占比来年化
        if actual_trading_days > 0 and days > 0:
            # 估计年化交易日数
            trading_days_per_year = (actual_trading_days / days) * 365
            annualized_volatility = np.std(returns, ddof=1) * np.sqrt(trading_days_per_year) if len(returns) > 1 else 0
        else:
            annualized_volatility = 0

        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(navs)

        # 夏普比率
        if actual_trading_days > 0:
            daily_rf_rate = self.risk_free_rate / trading_days_per_year
            excess_returns = returns - daily_rf_rate
            sharpe_ratio = (np.mean(excess_returns) * trading_days_per_year / annualized_volatility) if annualized_volatility > 0 else 0
        else:
            sharpe_ratio = 0

        # 索提诺比率（只考虑下行波动）
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 1 and actual_trading_days > 0:
            downside_volatility = np.std(downside_returns, ddof=1) * np.sqrt(trading_days_per_year)
            sortino_ratio = (annualized_return - self.risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
        else:
            sortino_ratio = 0

        # 卡玛比率
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 月度胜率 - 计算月度收益率为正的月份占比
        win_rate = self._calculate_monthly_win_rate(nav_series)

        return {
            "totalReturn": float(total_return),
            "annualizedReturn": float(annualized_return),
            "annualizedVolatility": float(annualized_volatility),
            "maxDrawdown": float(max_drawdown),
            "sharpeRatio": float(sharpe_ratio),
            "sortinoRatio": float(sortino_ratio),
            "calmarRatio": float(calmar_ratio),
            "winRate": float(win_rate)
        }

    def _get_empty_metrics(self) -> Dict[str, float]:
        """返回空指标"""
        return {
            "totalReturn": 0.0,
            "annualizedReturn": 0.0,
            "annualizedVolatility": 0.0,
            "maxDrawdown": 0.0,
            "sharpeRatio": 0.0,
            "sortinoRatio": 0.0,
            "calmarRatio": 0.0,
            "winRate": 0.0
        }

    def _calculate_monthly_win_rate(self, nav_series: Dict[str, float]) -> float:
        """
        计算月度胜率
        月度胜率 = 月度收益率为正的月份数 / 总月份数
        """
        if not nav_series:
            return 0.0

        # 获取每月末的净值
        monthly_end_nav = {}
        for date, nav in sorted(nav_series.items()):
            year_month = date[:7]  # YYYY-MM
            # 保留每月最后一个交易日的净值
            monthly_end_nav[year_month] = nav

        if len(monthly_end_nav) < 2:
            return 0.0

        # 计算月度收益率
        monthly_returns = []
        prev_nav = None

        for year_month in sorted(monthly_end_nav.keys()):
            current_nav = monthly_end_nav[year_month]

            if prev_nav is not None:
                monthly_return = (current_nav - prev_nav) / prev_nav
                monthly_returns.append(monthly_return)

            prev_nav = current_nav

        if len(monthly_returns) == 0:
            return 0.0

        # 计算胜率
        win_count = sum(1 for ret in monthly_returns if ret > 0)
        win_rate = win_count / len(monthly_returns)

        return win_rate

    def _calculate_max_drawdown(self, navs: List[float]) -> float:
        """
        计算最大回撤
        """
        if not navs or len(navs) < 2:
            return 0.0

        max_dd = 0.0
        peak = navs[0]

        for nav in navs:
            if nav > peak:
                peak = nav

            dd = (nav - peak) / peak
            if dd < max_dd:
                max_dd = dd

        return max_dd

    def _calculate_drawdown_curve(self, nav_series: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        计算回撤曲线
        """
        if not nav_series:
            return []

        dates = list(nav_series.keys())
        navs = list(nav_series.values())

        drawdown_curve = []
        peak = navs[0]

        for date, nav in zip(dates, navs):
            if nav > peak:
                peak = nav

            drawdown = (nav - peak) / peak
            drawdown_curve.append({
                "date": date,
                "drawdown": float(drawdown)
            })

        return drawdown_curve

    def _calculate_max_drawdown_info(self, nav_series: Dict[str, float]) -> Dict[str, Any]:
        """
        计算最大回撤的详细信息

        Returns:
            {
                "peakDate": "2024-01-15",  # 最大回撤开始日期（峰值）
                "valleyDate": "2024-03-20",  # 最大回撤发生日期（谷底）
                "recoveryDate": "2024-05-10" or None,  # 恢复日期（如果已恢复）
                "recoveryDays": 51 or None,  # 修复时间长度（天数）
                "maxDrawdown": -0.15  # 最大回撤值
            }
        """
        if not nav_series:
            return {
                "peakDate": None,
                "valleyDate": None,
                "recoveryDate": None,
                "recoveryDays": None,
                "maxDrawdown": 0.0
            }

        dates = sorted(nav_series.keys())
        navs = [nav_series[date] for date in dates]

        # 跟踪峰值和回撤
        peak = navs[0]
        peak_date = dates[0]
        max_drawdown = 0.0
        max_drawdown_peak_date = dates[0]
        max_drawdown_valley_date = dates[0]

        for i, (date, nav) in enumerate(zip(dates, navs)):
            if nav > peak:
                peak = nav
                peak_date = date

            drawdown = (nav - peak) / peak

            if drawdown < max_drawdown:
                max_drawdown = drawdown
                max_drawdown_peak_date = peak_date
                max_drawdown_valley_date = date

        # 查找恢复日期（从谷底开始，找到第一个净值 >= 峰值净值的日期）
        recovery_date = None
        valley_index = dates.index(max_drawdown_valley_date)
        peak_nav = nav_series[max_drawdown_peak_date]

        for i in range(valley_index + 1, len(dates)):
            if navs[i] >= peak_nav:
                recovery_date = dates[i]
                break

        # 计算修复时间长度
        recovery_days = None
        if recovery_date:
            valley_dt = datetime.strptime(max_drawdown_valley_date, '%Y-%m-%d')
            recovery_dt = datetime.strptime(recovery_date, '%Y-%m-%d')
            recovery_days = (recovery_dt - valley_dt).days

        return {
            "peakDate": max_drawdown_peak_date,
            "valleyDate": max_drawdown_valley_date,
            "recoveryDate": recovery_date,
            "recoveryDays": recovery_days,
            "maxDrawdown": float(max_drawdown)
        }

    def _calculate_yearly_returns(self, nav_series: Dict[str, float], start_date: str) -> List[Dict[str, Any]]:
        """
        计算年度收益

        Args:
            nav_series: 净值序列
            start_date: 回测开始日期，用于过滤掉开始日期之前的数据
        """
        if not nav_series:
            return []

        # 按年份分组，同时过滤掉开始日期之前的数据
        yearly_data = {}

        for date, nav in nav_series.items():
            # 过滤掉开始日期之前的数据
            if date < start_date:
                continue

            year = date[:4]
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].append((date, nav))

        # 计算每年的指标
        yearly_returns = []

        for year, data in sorted(yearly_data.items()):
            if len(data) < 2:
                continue

            data.sort(key=lambda x: x[0])
            dates = [d[0] for d in data]
            navs = [d[1] for d in data]

            # 年度收益率
            year_return = (navs[-1] - navs[0]) / navs[0]

            # 年度最大回撤
            year_max_dd = self._calculate_max_drawdown(navs)

            # 年度波动率 - 只计算有变化的日期
            returns = []
            actual_trading_days = 0
            for i in range(1, len(navs)):
                if navs[i] != navs[i-1]:
                    ret = (navs[i] - navs[i-1]) / navs[i-1]
                    returns.append(ret)
                    actual_trading_days += 1

            if len(returns) > 1 and actual_trading_days > 0:
                # 估计该年的交易日数
                days_in_year = (datetime.strptime(dates[-1], '%Y-%m-%d') - datetime.strptime(dates[0], '%Y-%m-%d')).days
                if days_in_year > 0:
                    trading_days_per_year = (actual_trading_days / days_in_year) * 365
                else:
                    trading_days_per_year = 252
                year_volatility = np.std(returns, ddof=1) * np.sqrt(trading_days_per_year)
            else:
                year_volatility = 0
                trading_days_per_year = 252

            # 年度夏普比率
            if len(returns) > 0 and year_volatility > 0:
                daily_rf_rate = self.risk_free_rate / trading_days_per_year
                excess_returns = np.array(returns) - daily_rf_rate
                year_sharpe = (np.mean(excess_returns) * trading_days_per_year / year_volatility)
            else:
                year_sharpe = 0

            yearly_returns.append({
                "year": year,
                "return": float(year_return),
                "maxDrawdown": float(year_max_dd),
                "volatility": float(year_volatility),
                "sharpeRatio": float(year_sharpe)
            })

        return yearly_returns

    def _calculate_position_info(self, nav_series: Dict[str, float], initial_capital: float) -> Dict[str, float]:
        """
        计算持仓信息

        Args:
            nav_series: 净值序列
            initial_capital: 初始资金（万元）

        Returns:
            持仓信息字典
        """
        if not nav_series or len(nav_series) == 0:
            return {
                "cost": 0.0,
                "marketValue": 0.0,
                "profit": 0.0,
                "profitRate": 0.0
            }

        # 持仓成本 = 初始资金
        cost = initial_capital

        # 持仓市值 = 初始资金 × 最新净值
        navs = list(nav_series.values())
        latest_nav = navs[-1]
        market_value = initial_capital * latest_nav

        # 持仓收益 = 持仓市值 - 持仓成本
        profit = market_value - cost

        # 持仓收益率 = (最新净值 - 1)
        profit_rate = latest_nav - 1.0

        return {
            "cost": float(cost),
            "marketValue": float(market_value),
            "profit": float(profit),
            "profitRate": float(profit_rate)
        }

    def _calculate_monthly_returns(self, nav_series: Dict[str, float], start_date: str) -> List[Dict[str, Any]]:
        """
        计算月度区间收益

        月度收益 = (本月末净值 - 上月末净值) / 上月末净值
        这样可以确保和产品分析页面的计算逻辑一致

        Args:
            nav_series: 净值序列
            start_date: 回测开始日期，用于过滤年份

        Returns:
            [
                {
                    "year": "2024",
                    "jan": 0.05,  # 1月收益率
                    "feb": -0.02,  # 2月收益率
                    ...
                    "dec": 0.03,  # 12月收益率
                    "annual": 0.15  # 全年收益率
                },
                ...
            ]
        """
        if not nav_series:
            return []

        # 提取开始年份
        start_year = start_date[:4]

        # 按日期排序
        sorted_dates = sorted(nav_series.keys())

        # 找到每个月的最后一天净值
        monthly_end_nav = {}  # key: 'YYYY-MM', value: nav
        for date in sorted_dates:
            year_month = date[:7]  # YYYY-MM
            monthly_end_nav[year_month] = nav_series[date]

        # 按年份分组
        years_months = sorted(monthly_end_nav.keys())
        years_dict = {}
        for ym in years_months:
            year = ym[:4]
            if year not in years_dict:
                years_dict[year] = []
            years_dict[year].append(ym)

        monthly_returns = []

        # 按年份倒序，只处理开始年份及之后的年份
        for year in sorted(years_dict.keys(), reverse=True):
            # 过滤掉开始日期之前的年份
            if year < start_year:
                continue
            year_data = {"year": year}
            month_keys = ["jan", "feb", "mar", "apr", "may", "jun",
                         "jul", "aug", "sep", "oct", "nov", "dec"]

            for month in range(1, 13):
                month_key = month_keys[month - 1]
                current_ym = f"{year}-{month:02d}"

                # 找到上个月的年月
                if month == 1:
                    prev_year = str(int(year) - 1)
                    prev_ym = f"{prev_year}-12"
                else:
                    prev_ym = f"{year}-{(month-1):02d}"

                # 计算月度收益
                if current_ym in monthly_end_nav:
                    if prev_ym in monthly_end_nav:
                        # 有上个月的数据，计算区间收益
                        month_return = (monthly_end_nav[current_ym] - monthly_end_nav[prev_ym]) / monthly_end_nav[prev_ym]
                        year_data[month_key] = float(month_return)
                    else:
                        # 没有上个月的数据，无法计算准确的月度收益
                        year_data[month_key] = None
                else:
                    # 当前月没有数据
                    year_data[month_key] = None

            # 计算全年收益
            if years_dict[year]:
                year_end_ym = max(years_dict[year])
                prev_year = str(int(year) - 1)
                year_start_ym = f"{prev_year}-12"

                if year_start_ym in monthly_end_nav:
                    # 有去年12月的数据，计算全年收益
                    annual_return = (monthly_end_nav[year_end_ym] - monthly_end_nav[year_start_ym]) / monthly_end_nav[year_start_ym]
                    year_data["annual"] = float(annual_return)
                else:
                    # 没有去年12月的数据，无法计算准确的全年收益
                    year_data["annual"] = None
            else:
                year_data["annual"] = None

            monthly_returns.append(year_data)

        return monthly_returns

    def _calculate_quarterly_contributions(
        self,
        nav_data: Dict[str, Dict[str, float]],
        weights: Dict[str, float],
        initial_capital: float,
        start_date: str
    ) -> List[Dict[str, Any]]:
        """
        计算季度收益贡献

        Args:
            nav_data: 各产品的净值数据 {'fund_code': {'date': nav, ...}}
            weights: 各产品的权重 {'fund_code': weight}
            initial_capital: 初始资金（万元）
            start_date: 回测开始日期

        Returns:
            [
                {
                    "quarter": "2024Q1",
                    "contributions": {
                        "fund_code_1": 12.5,  # 该产品在Q1的收益贡献（万元）
                        "fund_code_2": 8.3,
                        ...
                    },
                    "total": 20.8,  # 组合Q1总收益（万元）
                    "cumulative": 20.8  # 累计总收益（万元）
                },
                ...
            ]
        """
        if not nav_data or not weights:
            return []

        # 1. 找到所有日期并按季度分组
        all_dates = set()
        for fund_navs in nav_data.values():
            all_dates.update(fund_navs.keys())

        all_dates = sorted(all_dates)

        # 过滤掉开始日期之前的数据
        all_dates = [d for d in all_dates if d >= start_date]

        if not all_dates:
            return []

        # 2. 按季度分组日期
        def get_quarter(date_str: str) -> str:
            """获取日期所属季度，如 '2024Q1'"""
            year = date_str[:4]
            month = int(date_str[5:7])
            quarter = (month - 1) // 3 + 1
            return f"{year}Q{quarter}"

        # 找到每个季度的开始和结束日期
        quarters_dict = {}  # {'2024Q1': {'start': '2024-01-01', 'end': '2024-03-31', 'dates': [...]}}

        for date in all_dates:
            quarter = get_quarter(date)
            if quarter not in quarters_dict:
                quarters_dict[quarter] = {'dates': []}
            quarters_dict[quarter]['dates'].append(date)

        # 为每个季度确定开始和结束日期
        for quarter, data in quarters_dict.items():
            data['dates'].sort()
            data['start'] = data['dates'][0]
            data['end'] = data['dates'][-1]

        # 3. 计算每个季度的收益贡献
        quarterly_contributions = []
        cumulative_total = 0.0

        for quarter in sorted(quarters_dict.keys()):
            quarter_data = quarters_dict[quarter]
            quarter_start = quarter_data['start']
            quarter_end = quarter_data['end']

            contributions = {}
            quarter_total = 0.0

            # 计算每个产品的季度收益贡献
            for fund_code, weight in weights.items():
                if fund_code not in nav_data:
                    contributions[fund_code] = 0.0
                    continue

                fund_navs = nav_data[fund_code]

                # 获取季初和季末净值
                # 季初净值：取季度开始日期的净值，如果没有则取之前最近的净值
                start_nav = None
                for date in sorted(fund_navs.keys()):
                    if date <= quarter_start:
                        start_nav = fund_navs[date]
                    if date >= quarter_start:
                        break

                # 季末净值：取季度结束日期的净值
                end_nav = None
                for date in sorted(fund_navs.keys(), reverse=True):
                    if date <= quarter_end:
                        end_nav = fund_navs[date]
                        break

                if start_nav is None or end_nav is None:
                    contributions[fund_code] = 0.0
                    continue

                # 计算收益贡献
                # 单产品季度收益率
                product_return = (end_nav - start_nav) / start_nav

                # 单产品季度收益贡献金额（万元）= 收益率 * 权重 * 初始资金
                contribution = product_return * weight * initial_capital

                contributions[fund_code] = float(contribution)
                quarter_total += contribution

            # 累计收益
            cumulative_total += quarter_total

            quarterly_contributions.append({
                "quarter": quarter,
                "contributions": contributions,
                "total": float(quarter_total),
                "cumulative": float(cumulative_total)
            })

        return quarterly_contributions

    def _get_benchmark_curves(self, benchmark_code: str, start_date: str, end_date: str, portfolio_dates: list) -> tuple:
        """
        获取基准的净值曲线和回撤曲线，与组合日期点对齐

        Args:
            benchmark_code: 基准代码
            start_date: 开始日期
            end_date: 结束日期
            portfolio_dates: 组合的日期列表，用于对齐基准数据点

        Returns:
            (benchmark_nav_curve, benchmark_drawdown_curve)
        """
        try:
            import subprocess
            import urllib.parse
            import json
            from datetime import datetime, timedelta

            # 基准代码映射
            benchmark_map = {
                '000300': ('1.000300', '沪深300'),
                '000905': ('1.000905', '中证500'),
                '000001': ('1.000001', '上证指数'),
                '399006': ('0.399006', '创业板指'),
            }

            if benchmark_code not in benchmark_map:
                logger.warning(f"不支持的基准代码: {benchmark_code}")
                return None, None

            secid, name = benchmark_map[benchmark_code]

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
                '-A', 'Mozilla/5.0',
                '-H', 'Referer: https://quote.eastmoney.com/',
                '--compressed',
                full_url
            ]

            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                logger.error(f"获取基准数据失败: {result.stderr}")
                return None, None

            data = json.loads(result.stdout)

            if not data.get('data') or not data['data'].get('klines'):
                logger.error("基准数据格式错误")
                return None, None

            # 解析K线数据，构建日期到价格的映射
            klines = data['data']['klines']
            benchmark_data_map = {}
            for kline in klines:
                parts = kline.split(',')
                if len(parts) >= 2:
                    date_str = parts[0]
                    if start_date <= date_str <= end_date:
                        benchmark_data_map[date_str] = float(parts[1])

            if not benchmark_data_map:
                logger.warning(f"未找到基准数据在 {start_date} 到 {end_date} 范围内")
                return None, None

            # 对于组合的每个日期，找到对应或最近的基准数据
            benchmark_data = []
            for portfolio_date in portfolio_dates:
                # 将日期字符串转换为可比较的格式
                if isinstance(portfolio_date, str):
                    date_key = portfolio_date
                else:
                    date_key = portfolio_date

                # 首先尝试精确匹配
                if date_key in benchmark_data_map:
                    benchmark_data.append({
                        'date': date_key,
                        'value': benchmark_data_map[date_key]
                    })
                else:
                    # 如果没有精确匹配，先往前找最近的交易日
                    date_obj = datetime.strptime(date_key, '%Y-%m-%d')
                    found = False
                    for i in range(1, 8):  # 往前找最多7天
                        prev_date = (date_obj - timedelta(days=i)).strftime('%Y-%m-%d')
                        if prev_date in benchmark_data_map:
                            benchmark_data.append({
                                'date': date_key,  # 使用组合的日期
                                'value': benchmark_data_map[prev_date]
                            })
                            found = True
                            break

                    # 如果往前找不到，往后找
                    if not found:
                        for i in range(1, 8):  # 往后找最多7天
                            next_date = (date_obj + timedelta(days=i)).strftime('%Y-%m-%d')
                            if next_date in benchmark_data_map:
                                benchmark_data.append({
                                    'date': date_key,  # 使用组合的日期
                                    'value': benchmark_data_map[next_date]
                                })
                                found = True
                                break

                    if not found:
                        logger.warning(f"未找到日期 {date_key} 附近的基准数据")

            if not benchmark_data:
                return None, None

            # 归一化到1.0开始
            first_value = benchmark_data[0]['value']
            benchmark_nav_curve = [
                {
                    'date': item['date'],
                    'nav': item['value'] / first_value
                }
                for item in benchmark_data
            ]

            # 计算回撤曲线
            benchmark_drawdown_curve = []
            peak = 1.0
            for item in benchmark_nav_curve:
                nav = item['nav']
                if nav > peak:
                    peak = nav
                drawdown = (nav - peak) / peak
                benchmark_drawdown_curve.append({
                    'date': item['date'],
                    'drawdown': drawdown
                })

            logger.info(f"成功获取基准 {name} 数据，共 {len(benchmark_nav_curve)} 个点（与组合日期对齐）")
            return benchmark_nav_curve, benchmark_drawdown_curve

        except Exception as e:
            logger.error(f"获取基准数据失败: {str(e)}", exc_info=True)
            return None, None

    def _analyze_new_highs(self, portfolio_nav_series: dict, benchmark_nav_curve: list = None) -> dict:
        """
        分析组合净值创新高事件

        Args:
            portfolio_nav_series: 组合净值序列 {date: nav}
            benchmark_nav_curve: 基准净值曲线 [{date: str, nav: float}]

        Returns:
            {
                "records": [...],  # 创新高记录列表
                "summary": {...}   # 分析总结
            }
        """
        try:
            from datetime import datetime

            # 将净值序列转换为列表
            nav_list = [{"date": date, "nav": nav} for date, nav in portfolio_nav_series.items()]
            
            if len(nav_list) < 2:
                return {
                    "records": [],
                    "summary": {
                        "totalHighs": 0,
                        "pattern": "数据不足",
                        "marketDependency": "无法判断"
                    }
                }

            # 构建基准数据映射
            benchmark_map = {}
            if benchmark_nav_curve:
                for item in benchmark_nav_curve:
                    benchmark_map[item['date']] = item['nav']

            # 查找所有创新高点
            new_high_records = []
            peak_nav = nav_list[0]['nav']
            last_high_date = None
            last_high_index = 0
            last_benchmark_nav = benchmark_map.get(nav_list[0]['date'], 1.0) if benchmark_map else 1.0

            for i, item in enumerate(nav_list):
                current_nav = item['nav']
                current_date = item['date']
                
                if current_nav > peak_nav:
                    # 发现新高
                    peak_nav = current_nav
                    
                    # 计算距上次新高天数
                    days_since_last_high = None
                    if last_high_date:
                        date1 = datetime.strptime(last_high_date, '%Y-%m-%d')
                        date2 = datetime.strptime(current_date, '%Y-%m-%d')
                        days_since_last_high = (date2 - date1).days

                    # 计算期间指数涨跌
                    benchmark_change = None
                    if benchmark_map and current_date in benchmark_map:
                        current_benchmark_nav = benchmark_map[current_date]
                        if last_benchmark_nav > 0:
                            benchmark_change = (current_benchmark_nav / last_benchmark_nav - 1) * 100
                        last_benchmark_nav = current_benchmark_nav

                    # 计算此后最大回撤和修复天数
                    subsequent_max_drawdown = 0.0
                    drawdown_recovery_days = None
                    
                    if i < len(nav_list) - 1:
                        # 计算从当前新高到下一个新高（或结束）之间的最大回撤
                        max_dd = 0.0
                        recovery_date = None
                        
                        for j in range(i + 1, len(nav_list)):
                            future_nav = nav_list[j]['nav']
                            dd = (future_nav - peak_nav) / peak_nav
                            if dd < max_dd:
                                max_dd = dd
                            
                            # 如果净值回到或超过新高点，记录修复日期
                            if future_nav >= peak_nav and recovery_date is None:
                                recovery_date = nav_list[j]['date']
                                break
                            
                            # 如果有新的更高点，停止
                            if future_nav > peak_nav:
                                break
                        
                        subsequent_max_drawdown = max_dd * 100
                        
                        # 计算修复天数
                        if recovery_date:
                            date1 = datetime.strptime(current_date, '%Y-%m-%d')
                            date2 = datetime.strptime(recovery_date, '%Y-%m-%d')
                            drawdown_recovery_days = (date2 - date1).days

                    # 判断标签（按优先级依次判断）
                    tag = None
                    tag_emoji = None

                    # 1. 压力极限：此后最大回撤 ≤ -10%
                    if subsequent_max_drawdown <= -10:
                        tag = "压力测试"
                        tag_emoji = "🔴"
                    # 2. 艰难修复：此后最大回撤 ≤ -3% 且 回撤修复天数 ≥ 60天
                    elif subsequent_max_drawdown <= -3 and drawdown_recovery_days is not None and drawdown_recovery_days >= 60:
                        tag = "漫长调整"
                        tag_emoji = "🟡"
                    # 3. 关键突破：距上次新高天数 ≥ 90天
                    elif days_since_last_high is not None and days_since_last_high >= 90:
                        tag = "趋势突破"
                        tag_emoji = "🟢"
                    # 4. 独立阿尔法：期间指数涨跌 ≤ -3% 但基金创出新高
                    elif benchmark_change is not None and benchmark_change <= -3:
                        tag = "逆势创高"
                        tag_emoji = "🟦"
                    else:
                        # 稳健期，不展示
                        tag = "稳健期"
                        tag_emoji = None

                    # 添加记录
                    record = {
                        "序号": len(new_high_records) + 1,
                        "创新高日期": current_date,
                        "净值": round(current_nav, 4),
                        "距上次新高天数": days_since_last_high,
                        "期间指数涨跌": round(benchmark_change, 2) if benchmark_change is not None else None,
                        "此后最大回撤": round(subsequent_max_drawdown, 2),
                        "回撤修复天数": drawdown_recovery_days,
                        "标签": tag,
                        "标签符号": tag_emoji,
                        "备注": self._get_market_remark(benchmark_change, subsequent_max_drawdown)
                    }

                    new_high_records.append(record)
                    last_high_date = current_date
                    last_high_index = i

            # 生成分析总结
            summary = self._generate_new_high_summary(new_high_records, benchmark_map is not None)

            # 筛选出关键事件（排除"稳健期"）
            key_events = [r for r in new_high_records if r["标签"] != "稳健期"]

            # 合并时间过近的关键事件
            merged_key_events = self._merge_nearby_key_events(key_events)


            # 统计各类关键事件数量（基于合并后的事件）
            tag_counts = {
                "压力测试": 0,
                "漫长调整": 0,
                "趋势突破": 0,
                "逆势创高": 0
            }
            for event in merged_key_events:
                # 如果是合并事件，可能有多个标签
                tags = event["标签"].split("+")
                for tag in tags:
                    if tag in tag_counts:
                        tag_counts[tag] += 1

            summary["keyEventCount"] = len(merged_key_events)
            summary["tagCounts"] = tag_counts

            return {
                "records": new_high_records,  # 完整记录
                "keyEvents": merged_key_events,  # 关键事件（合并后，用于前端展示）
                "summary": summary
            }

        except Exception as e:
            logger.error(f"创新高分析失败: {str(e)}", exc_info=True)
            return {
                "records": [],
                "keyEvents": [],
                "summary": {
                    "totalHighs": 0,
                    "keyEventCount": 0,
                    "pattern": "分析失败",
                    "marketDependency": "无法判断",
                    "tagCounts": {
                        "压力测试": 0,
                        "漫长调整": 0,
                        "趋势突破": 0,
                        "逆势创高": 0
                    }
                }
            }

    def _merge_nearby_key_events(self, key_events: list, merge_threshold_days: int = 7) -> list:
        """
        合并时间过近的关键事件，真正合并两个事件的影响

        Args:
            key_events: 关键事件列表
            merge_threshold_days: 合并阈值（天），默认7天

        Returns:
            合并后的关键事件列表
        """
        if len(key_events) <= 1:
            return key_events

        from datetime import datetime

        # 按日期排序
        sorted_events = sorted(key_events, key=lambda x: x["创新高日期"])

        merged = []
        i = 0

        while i < len(sorted_events):
            first_event = sorted_events[i].copy()
            merged_tags = [first_event["标签"]]
            merged_emojis = [first_event["标签符号"]]
            merged_events_info = []  # 记录被合并的事件信息

            # 保留第一个事件的关键数据
            first_days_since_last = first_event["距上次新高天数"]
            cumulative_benchmark_change = first_event["期间指数涨跌"] if first_event["期间指数涨跌"] is not None else 0

            # 向后查找需要合并的事件
            j = i + 1
            last_event = first_event

            while j < len(sorted_events):
                next_event = sorted_events[j]

                # 计算时间间隔
                date1 = datetime.strptime(last_event["创新高日期"], '%Y-%m-%d')
                date2 = datetime.strptime(next_event["创新高日期"], '%Y-%m-%d')
                days_diff = (date2 - date1).days

                if days_diff <= merge_threshold_days:
                    # 需要合并
                    merged_events_info.append({
                        "日期": next_event["创新高日期"],
                        "标签": next_event["标签"],
                        "距上次": days_diff
                    })

                    merged_tags.append(next_event["标签"])
                    merged_emojis.append(next_event["标签符号"])

                    # 累计指数涨跌
                    if next_event["期间指数涨跌"] is not None:
                        cumulative_benchmark_change += next_event["期间指数涨跌"]

                    # 保留最后一个事件作为基准
                    last_event = next_event
                    j += 1
                else:
                    break

            # 构建合并后的事件
            if len(merged_tags) > 1:
                # 发生了合并
                # 合并标签（去重）
                unique_tags = []
                seen = set()
                for tag in merged_tags:
                    if tag not in seen:
                        unique_tags.append(tag)
                        seen.add(tag)

                # 合并emoji
                unique_emojis = []
                seen_emojis = set()
                for emoji in merged_emojis:
                    if emoji and emoji not in seen_emojis:
                        unique_emojis.append(emoji)
                        seen_emojis.add(emoji)

                # 构建合并事件
                merged_event = last_event.copy()  # 使用最后一个事件的大部分数据
                merged_event["标签"] = "+".join(unique_tags)
                merged_event["标签符号"] = "".join(unique_emojis)

                # 关键：使用第一个事件的"距上次新高天数"
                merged_event["距上次新高天数"] = first_days_since_last

                # 使用累计的指数涨跌
                merged_event["期间指数涨跌"] = round(cumulative_benchmark_change, 2) if cumulative_benchmark_change != 0 else None

                # "此后最大回撤"和"回撤修复天数"使用最后一个事件的值（从最后一个新高往后算）
                # 这些已经在last_event中了

                # 在备注中添加合并信息
                merge_details = []
                for info in merged_events_info:
                    merge_details.append(f"{info['距上次']}天后{info['日期']}的{info['标签']}")

                merge_note = "（合并事件：" + "、".join(merge_details) + "）"
                merged_event["备注"] = merged_event["备注"] + " " + merge_note

                logger.info(f"合并关键事件: {first_event['创新高日期']} ~ {last_event['创新高日期']}, 合并了 {len(merged_events_info)} 个后续事件")

                merged.append(merged_event)
            else:
                # 没有合并，保持原样
                merged.append(first_event)

            i = j  # 跳过已合并的事件

        return merged

    def _get_market_remark(self, benchmark_change: float = None, max_drawdown: float = 0) -> str:
        """生成市场环境备注"""
        remarks = []
        
        if benchmark_change is not None:
            if benchmark_change > 5:
                remarks.append("市场强势上涨")
            elif benchmark_change > 0:
                remarks.append("市场温和上涨")
            elif benchmark_change > -5:
                remarks.append("市场震荡")
            else:
                remarks.append("市场下跌")
        
        if max_drawdown < -10:
            remarks.append("后续大幅回撤")
        elif max_drawdown < -5:
            remarks.append("后续中度回撤")
        elif max_drawdown < -2:
            remarks.append("后续小幅回撤")
        else:
            remarks.append("走势稳健")
        
        return "；".join(remarks) if remarks else "-"

    def _generate_new_high_summary(self, records: list, has_benchmark: bool) -> dict:
        """生成创新高分析总结"""
        if not records:
            return {
                "totalHighs": 0,
                "pattern": "未创新高",
                "marketDependency": "无法判断",
                "avgDaysBetweenHighs": None,
                "avgDrawdown": None
            }

        total_highs = len(records)
        
        # 计算平均间隔天数（排除第一个）
        days_list = [r["距上次新高天数"] for r in records if r["距上次新高天数"] is not None]
        avg_days = round(sum(days_list) / len(days_list), 1) if days_list else None

        # 计算平均回撤
        drawdown_list = [r["此后最大回撤"] for r in records if r["此后最大回撤"] is not None]
        avg_drawdown = round(sum(drawdown_list) / len(drawdown_list), 2) if drawdown_list else None

        # 判断模式
        pattern = "稳健攀升型"
        if avg_days and avg_drawdown:
            if avg_days < 60 and avg_drawdown > -8:
                pattern = "稳健攀升型（间隔短、回撤浅）"
            elif avg_days < 60 and avg_drawdown <= -8:
                pattern = "快速波动型（间隔短、回撤深）"
            elif avg_days >= 60 and avg_drawdown > -8:
                pattern = "缓慢上升型（间隔长、回撤浅）"
            else:
                pattern = "波动冲刺型（间隔长、回撤深）"

        # 判断市场依赖度
        market_dependency = "无法判断"
        if has_benchmark:
            # 统计顺风创新高（指数上涨）和逆风创新高（指数下跌）的次数
            with_market = 0  # 指数涨时创新高
            against_market = 0  # 指数跌时创新高
            
            for r in records:
                if r["期间指数涨跌"] is not None:
                    if r["期间指数涨跌"] > 0:
                        with_market += 1
                    else:
                        against_market += 1
            
            total_with_benchmark = with_market + against_market
            if total_with_benchmark > 0:
                with_market_pct = (with_market / total_with_benchmark) * 100
                
                if with_market_pct >= 70:
                    market_dependency = f"β驱动为主（{with_market_pct:.0f}%顺风创新高）"
                elif with_market_pct >= 40:
                    market_dependency = f"α+β均衡（{with_market_pct:.0f}%顺风创新高）"
                else:
                    market_dependency = f"α驱动为主（{100-with_market_pct:.0f}%逆风创新高）"

        return {
            "totalHighs": total_highs,
            "pattern": pattern,
            "marketDependency": market_dependency,
            "avgDaysBetweenHighs": avg_days,
            "avgDrawdown": avg_drawdown
        }

    async def _get_product_benchmark_curves(
        self,
        db: Session,
        product_code: str,
        start_date: str,
        end_date: str,
        portfolio_dates: list
    ) -> tuple:
        """
        获取产品作为基准的净值曲线和回撤曲线，与组合日期点对齐

        Args:
            db: 数据库会话
            product_code: 产品代码
            start_date: 开始日期
            end_date: 结束日期
            portfolio_dates: 组合的日期列表，用于对齐基准数据点

        Returns:
            (benchmark_nav_curve, benchmark_drawdown_curve)
        """
        try:
            # 查询产品的净值数据
            navs = db.query(Nav).filter(
                and_(
                    Nav.fund_code == product_code,
                    Nav.nav_date >= start_date,
                    Nav.nav_date <= end_date
                )
            ).order_by(Nav.nav_date).all()

            if not navs:
                logger.warning(f"产品 {product_code} 在指定时间范围内没有净值数据")
                return None, None

            # 构建产品净值数据映射
            product_data_map = {}
            for nav in navs:
                date_str = nav.nav_date.strftime('%Y-%m-%d')
                product_data_map[date_str] = float(nav.accum_nav)

            # 对于组合的每个日期，找到对应或最近的产品净值
            benchmark_data = []
            for portfolio_date in portfolio_dates:
                date_key = portfolio_date if isinstance(portfolio_date, str) else portfolio_date

                # 首先尝试精确匹配
                if date_key in product_data_map:
                    benchmark_data.append({
                        'date': date_key,
                        'value': product_data_map[date_key]
                    })
                else:
                    # 如果没有精确匹配，往前找最近的交易日
                    from datetime import datetime, timedelta
                    current_date = datetime.strptime(date_key, '%Y-%m-%d')
                    found = False

                    # 往前找最多10天
                    for i in range(1, 11):
                        prev_date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
                        if prev_date in product_data_map:
                            benchmark_data.append({
                                'date': date_key,
                                'value': product_data_map[prev_date]
                            })
                            found = True
                            break

                    if not found:
                        logger.warning(f"未找到日期 {date_key} 附近的产品净值数据")

            if not benchmark_data:
                logger.warning(f"产品 {product_code} 没有可用的基准数据")
                return None, None

            # 计算归一化净值（以第一个值为基准=1.0）
            first_value = benchmark_data[0]['value']
            benchmark_nav_curve = []
            for item in benchmark_data:
                normalized_nav = item['value'] / first_value
                benchmark_nav_curve.append({
                    'date': item['date'],
                    'nav': normalized_nav
                })

            # 计算回撤曲线
            benchmark_drawdown_curve = []
            peak = 0
            for item in benchmark_nav_curve:
                nav = item['nav']
                if nav > peak:
                    peak = nav
                drawdown = (nav - peak) / peak if peak > 0 else 0
                benchmark_drawdown_curve.append({
                    'date': item['date'],
                    'drawdown': drawdown
                })

            logger.info(f"成功获取产品 {product_code} 基准数据，共 {len(benchmark_nav_curve)} 个点（与组合日期对齐）")
            return benchmark_nav_curve, benchmark_drawdown_curve

        except Exception as e:
            logger.error(f"获取产品基准数据失败: {str(e)}", exc_info=True)
            return None, None

    def _extract_weekly_nav(self, nav_series: Dict[str, float]) -> List[Dict]:
        """
        从日度净值序列中提取周度净值（每周五或最后交易日）

        Args:
            nav_series: 日度净值序列 {'2024-01-01': 1.0, '2024-01-02': 1.01, ...}

        Returns:
            周度净值列表 [
                {
                    'date': '2024-01-05',
                    'unit_nav': 1.01,
                    'accum_nav': 1.01,
                    'total_return': 1.0
                },
                ...
            ]
        """
        if not nav_series:
            return []

        # 转换为 DataFrame 便于处理
        df = pd.DataFrame([
            {'date': date, 'nav': nav}
            for date, nav in sorted(nav_series.items())
        ])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # 按周重采样，取每周最后一个交易日
        weekly_df = df.resample('W-FRI').last()

        # 删除空值（没有交易的周）
        weekly_df = weekly_df.dropna()

        # 转换为列表
        weekly_navs = []
        initial_nav = 1.0  # 初始净值

        for date, row in weekly_df.iterrows():
            nav = float(row['nav'])
            total_return = (nav - initial_nav) / initial_nav * 100  # 累计收益率（%）

            weekly_navs.append({
                'date': date.strftime('%Y-%m-%d'),
                'unit_nav': nav,
                'accum_nav': nav,  # 对于回测组合，单位净值=累计净值
                'total_return': total_return
            })

        logger.info(f"从 {len(nav_series)} 个日度净值中提取了 {len(weekly_navs)} 个周度净值")
        return weekly_navs

