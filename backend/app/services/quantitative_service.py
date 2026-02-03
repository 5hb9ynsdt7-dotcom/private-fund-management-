"""
量化分析服务
包含指数数据获取、超额收益计算、风险指标计算等功能
"""
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import subprocess
import urllib.parse
from sqlalchemy.orm import Session


class QuantitativeService:
    """量化分析服务类"""

    def __init__(self, db=None):
        self.index_cache = {}  # 缓存指数数据
        self.db = db  # 数据库会话

    async def fetch_index_data(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        获取指数数据（从东方财富API）
        使用收盘点位（价格指数）
        """
        try:
            # 构建东方财富API URL
            base_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

            # 转换指数代码格式
            secid = self._get_secid(index_code)

            # 使用简化参数获取数据（参考成功案例）
            params = {
                "secid": secid,
                "fields1": "f1",
                "fields2": "f51,f53",  # f51=日期, f53=收盘价
                "klt": "101",  # 日K线
                "fqt": "1",  # 复权
                "end": "20500101",  # 结束日期设为未来
                "lmt": "3000"  # 获取最近3000条数据（约12年）
            }

            # 使用curl获取数据（绕过Python SSL库问题）
            # 构建完整URL
            query_string = urllib.parse.urlencode(params)
            full_url = f"{base_url}?{query_string}"

            # 使用curl命令
            curl_cmd = [
                'curl',
                '-s',  # 静默模式
                '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15',
                '-H', 'Referer: https://quote.eastmoney.com/zs000905.html',
                '-H', 'Accept: */*',
                '--compressed',  # 自动处理gzip
                full_url
            ]

            try:
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=15)
                if result.returncode != 0:
                    print(f"curl请求失败: {result.stderr}")
                    return self._generate_mock_index_data(index_code, start_date, end_date)

                response_text = result.stdout

                # 解析JSON响应（处理JSONP格式）
                if "(" in response_text and ")" in response_text:
                    json_str = response_text[response_text.find("(") + 1:response_text.rfind(")")]
                    data = json.loads(json_str)
                else:
                    data = json.loads(response_text)

            except subprocess.TimeoutExpired:
                print("curl请求超时")
                return self._generate_mock_index_data(index_code, start_date, end_date)
            except Exception as e:
                print(f"curl请求异常: {e}")
                return self._generate_mock_index_data(index_code, start_date, end_date)

            if data.get("data") and data["data"].get("klines"):
                index_data = []
                klines = data["data"]["klines"]

                for kline in klines:
                    fields = kline.split(",")
                    # 使用简化字段：fields2=f51,f53 -> [日期, 收盘价]
                    date_str = fields[0]
                    close_price = float(fields[1]) if len(fields) > 1 else 0

                    # 格式化日期
                    if len(date_str) == 8:  # YYYYMMDD格式
                        date_obj = datetime.strptime(date_str, "%Y%m%d")
                        date_str = date_obj.strftime("%Y-%m-%d")

                    index_data.append({
                        "date": date_str,
                        "value": close_price,  # 收盘价
                        "open": close_price,   # 简化版本，其他字段用收盘价填充
                        "high": close_price,
                        "low": close_price,
                        "volume": 0
                    })

                # 如果指定了日期范围，过滤数据
                if start_date or end_date:
                    filtered_data = []
                    for item in index_data:
                        item_date = datetime.strptime(item['date'], "%Y-%m-%d")
                        if start_date:
                            start_dt = datetime.strptime(start_date.replace("-", ""), "%Y%m%d")
                            if item_date < start_dt:
                                continue
                        if end_date:
                            end_dt = datetime.strptime(end_date.replace("-", ""), "%Y%m%d")
                            if item_date > end_dt:
                                continue
                        filtered_data.append(item)
                    index_data = filtered_data

                print(f"成功获取指数 {index_code} 的数据，共 {len(index_data)} 条")

                # 输出关键日期的数据用于调试
                for item in index_data:
                    if '2024-12-27' in item['date'] or '2025-01-27' in item['date']:
                        print(f"  关键日期: {item['date']}, 收盘: {item['value']}")

                return index_data

            # 如果API失败，返回模拟数据
            print(f"东方财富API返回数据为空，使用模拟数据")
            return self._generate_mock_index_data(index_code, start_date, end_date)

        except Exception as e:
            print(f"获取指数数据失败: {e}")
            # 返回模拟数据
            return self._generate_mock_index_data(index_code, start_date, end_date)

    def _get_secid(self, index_code: str) -> str:
        """
        转换指数代码为东方财富格式
        secid规则：0.xxxxxx (深市/中证), 1.xxxxxx (沪市)
        """
        code_map = {
            "000905.SH": "0.399905",  # 中证500（深市代码）✓
            "000300.SH": "1.000300",  # 沪深300（沪市）
            "399300.SZ": "0.399300",  # 沪深300（深市代码，备用）
            "000906.SH": "1.000906",  # 中证800（沪市）
            "000510.SH": "1.000510",  # 中证A500（沪市）
            "000852.SH": "1.000852",  # 中证1000（沪市）
            "399852.SZ": "0.399852",  # 中证1000（深市代码，备用）
            "932000.CS": "1.932000",  # 中证2000
            "932000.CSI": "1.932000", # 中证2000（备用）
            "000001.SH": "1.000001",  # 上证指数（沪市）
        }
        return code_map.get(index_code, "0.399905")

    def _generate_mock_index_data(
        self,
        index_code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict]:
        """
        生成模拟指数数据（用于测试）
        """
        if not start_date or not end_date:
            # 如果没有提供日期，使用最近一年的数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # 转换日期格式（支持YYYYMMDD和YYYY-MM-DD两种格式）
        if start_date and len(start_date) == 8 and "-" not in start_date:
            start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
        if end_date and len(end_date) == 8 and "-" not in end_date:
            end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"

        # 生成日期序列
        date_range = pd.date_range(start=start_date, end=end_date, freq="B")

        # 生成模拟数据
        base_value = {
            "399905.SZ": 5000,  # 中证500
            "399300.SZ": 4000,  # 沪深300
            "000906.SH": 3000,  # 中证800
            "000510.SH": 2000,  # 中证A500
            "399852.SZ": 6000,  # 中证1000
        }.get(index_code, 5000)

        index_data = []
        current_value = base_value

        for date in date_range:
            # 生成随机涨跌
            daily_return = np.random.normal(0.0002, 0.015)  # 日均0.02%，波动1.5%
            current_value *= (1 + daily_return)

            index_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(current_value, 2),
                "open": round(current_value * 0.995, 2),
                "high": round(current_value * 1.01, 2),
                "low": round(current_value * 0.99, 2),
                "volume": np.random.randint(1000000, 10000000)
            })

        return index_data

    def _find_closest_nav(self, nav_df: pd.DataFrame, target_date: pd.Timestamp, direction: str = 'backward', max_days: int = 45) -> Optional[pd.Series]:
        """
        查找最接近目标日期的净值
        direction: 'backward' 向前查找（在目标日期之前），'forward' 向后查找（在目标日期之后）
        max_days: 最大查找天数，防止跨度过大（默认45天，约1.5个月）
        """
        if direction == 'backward':
            # 查找目标日期或之前最近的净值，但限制在max_days天内
            min_date = target_date - pd.Timedelta(days=max_days)
            valid_navs = nav_df[(nav_df['date'] <= target_date) & (nav_df['date'] >= min_date)]
            if len(valid_navs) > 0:
                return valid_navs.iloc[-1]
        else:
            # 查找目标日期或之后最近的净值，但限制在max_days天内
            max_date = target_date + pd.Timedelta(days=max_days)
            valid_navs = nav_df[(nav_df['date'] >= target_date) & (nav_df['date'] <= max_date)]
            if len(valid_navs) > 0:
                return valid_navs.iloc[0]

        return None

    def _align_data_by_date(self, nav_df: pd.DataFrame, index_df: pd.DataFrame, target_date: pd.Timestamp, direction: str = 'backward') -> Optional[Dict]:
        """
        严格按日期对齐净值和指数数据
        返回对齐后的数据: {"date": ..., "nav": ..., "index": ...}
        """
        # 查找目标日期对应的净值
        nav_row = self._find_closest_nav(nav_df, target_date, direction)

        if nav_row is None:
            return None

        # 使用净值的实际日期来查找指数
        nav_date = nav_row['date']

        # 查找同一天的指数数据
        index_row = index_df[index_df['date'] == nav_date]

        if len(index_row) == 0:
            return None

        return {
            "date": nav_date,
            "nav": nav_row['nav'],
            "index": index_row.iloc[0]['value']
        }

    def _get_weekly_nav_dates(self, nav_df: pd.DataFrame, month_start: pd.Timestamp, month_end: pd.Timestamp) -> List[pd.Timestamp]:
        """
        获取月度内的周度净值更新日期
        周度定义：周五到周五（遇到长假特殊处理）
        """
        # 筛选月度范围内的净值日期
        month_navs = nav_df[(nav_df['date'] >= month_start) & (nav_df['date'] <= month_end)].copy()

        if len(month_navs) == 0:
            return []

        # 返回所有净值日期（按周五优先排序，但保留所有更新日）
        return month_navs['date'].tolist()

    def calculate_monthly_excess(
        self,
        nav_data: List,
        index_data: List[Dict],
        year: int,
        fund_code: str = None
    ) -> Dict[str, Any]:
        """
        计算月度超额收益
        使用周复利累计方法：月度超额 = [(1+周1超额)×(1+周2超额)×...×(1+周n超额)] - 1
        使用复权累计净值（adjusted_accum_nav），自动考虑分红影响
        """
        # 转换为DataFrame（使用复权累计净值）
        nav_df = pd.DataFrame([{
            "date": pd.to_datetime(nav.nav_date),
            "nav": float(nav.adjusted_accum_nav) if nav.adjusted_accum_nav else float(nav.unit_nav),
            "fund_code": fund_code
        } for nav in nav_data])

        index_df = pd.DataFrame(index_data)
        index_df['date'] = pd.to_datetime(index_df['date'])

        # 按日期排序
        nav_df = nav_df.sort_values('date').reset_index(drop=True)
        index_df = index_df.sort_values('date').reset_index(drop=True)

        monthly_results = {}
        win_count = 0
        total_count = 0

        # 计算每月超额收益
        for month in range(1, 13):
            # 确定月末日期
            if month == 12:
                month_end = pd.Timestamp(year, 12, 31)
            else:
                month_end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)

            # 确定月初日期（上月月末）
            month_start = pd.Timestamp(year, month, 1) - pd.Timedelta(days=1)
            if month == 1:
                # 1月的期初是上一年12月31日
                month_start = pd.Timestamp(year - 1, 12, 31)

            # 获取期初数据
            period_start_data = self._align_data_by_date(nav_df, index_df, month_start, 'backward')
            if period_start_data is None:
                monthly_results[f"month{month}"] = None
                continue

            # 获取月度内所有周度净值日期
            month_begin = pd.Timestamp(year, month, 1)
            weekly_dates = self._get_weekly_nav_dates(nav_df, month_begin, month_end)

            if len(weekly_dates) == 0:
                monthly_results[f"month{month}"] = None
                continue

            # 按周计算超额收益并复利累计
            compound_factor = 1.0
            prev_date = period_start_data['date']
            prev_nav = period_start_data['nav']
            prev_index = period_start_data['index']

            for week_end_date in weekly_dates:
                # 获取周末数据
                week_end_data = self._align_data_by_date(nav_df, index_df, week_end_date, 'backward')

                if week_end_data is None:
                    continue

                # 使用复权累计净值，直接计算周收益率（不需要手动分红调整）
                nav_return = (week_end_data['nav'] / prev_nav - 1)
                index_return = (week_end_data['index'] / prev_index - 1)
                weekly_excess = nav_return - index_return

                # 复利累计
                compound_factor *= (1 + weekly_excess)

                # 更新为下一周的期初
                prev_date = week_end_data['date']
                prev_nav = week_end_data['nav']
                prev_index = week_end_data['index']

            # 计算月度超额收益
            monthly_excess = (compound_factor - 1) * 100
            monthly_results[f"month{month}"] = round(monthly_excess, 2)

            total_count += 1
            if monthly_excess > 0:
                win_count += 1

        # 计算胜率
        win_rate = round((win_count / total_count * 100) if total_count > 0 else 0, 1)

        # 计算年度累计（使用月度复利）
        valid_returns = [v for v in monthly_results.values() if v is not None]
        if valid_returns:
            year_compound = 1.0
            for monthly_excess in valid_returns:
                year_compound *= (1 + monthly_excess / 100)
            year_total = round((year_compound - 1) * 100, 2)
        else:
            year_total = 0

        monthly_results['yearTotal'] = year_total
        monthly_results['winRate'] = win_rate

        return monthly_results

    def calculate_yearly_excess(
        self,
        nav_data: List,
        index_data: List[Dict],
        years: List[int],
        fund_code: str = None
    ) -> Dict[str, Any]:
        """
        计算年度超额收益
        使用月度复利累计方法：年度超额 = [(1+月1超额)×(1+月2超额)×...×(1+月12超额)] - 1
        使用复权累计净值（adjusted_accum_nav），自动考虑分红影响
        """
        # 转换为DataFrame（使用复权累计净值）
        nav_df = pd.DataFrame([{
            "date": pd.to_datetime(nav.nav_date),
            "nav": float(nav.adjusted_accum_nav) if nav.adjusted_accum_nav else float(nav.unit_nav)
        } for nav in nav_data])

        index_df = pd.DataFrame(index_data)
        index_df['date'] = pd.to_datetime(index_df['date'])

        # 按日期排序
        nav_df = nav_df.sort_values('date').reset_index(drop=True)
        index_df = index_df.sort_values('date').reset_index(drop=True)

        yearly_results = {}

        for year in years:
            # 计算该年度的12个月的月度超额
            monthly_excess_list = []

            for month in range(1, 13):
                # 确定月末日期
                if month == 12:
                    month_end = pd.Timestamp(year, 12, 31)
                else:
                    month_end = pd.Timestamp(year, month + 1, 1) - pd.Timedelta(days=1)

                # 确定月初日期（上月月末）
                month_start = pd.Timestamp(year, month, 1) - pd.Timedelta(days=1)
                if month == 1:
                    # 1月的期初是上一年12月31日
                    month_start = pd.Timestamp(year - 1, 12, 31)

                # 获取期初数据
                period_start_data = self._align_data_by_date(nav_df, index_df, month_start, 'backward')
                if period_start_data is None:
                    continue

                # 获取月度内所有周度净值日期
                month_begin = pd.Timestamp(year, month, 1)
                weekly_dates = self._get_weekly_nav_dates(nav_df, month_begin, month_end)

                if len(weekly_dates) == 0:
                    continue

                # 按周计算超额收益并复利累计
                compound_factor = 1.0
                prev_nav = period_start_data['nav']
                prev_index = period_start_data['index']

                for week_end_date in weekly_dates:
                    # 获取周末数据
                    week_end_data = self._align_data_by_date(nav_df, index_df, week_end_date, 'backward')

                    if week_end_data is None:
                        continue

                    # 使用复权累计净值，直接计算周收益率（不需要手动分红调整）
                    nav_return = (week_end_data['nav'] / prev_nav - 1)
                    index_return = (week_end_data['index'] / prev_index - 1)
                    weekly_excess = nav_return - index_return

                    # 复利累计
                    compound_factor *= (1 + weekly_excess)

                    # 更新为下一周的期初
                    prev_nav = week_end_data['nav']
                    prev_index = week_end_data['index']

                # 计算月度超额收益
                monthly_excess = (compound_factor - 1) * 100
                monthly_excess_list.append(monthly_excess)

            # 使用月度超额进行复利累计，得到年度超额
            if len(monthly_excess_list) > 0:
                year_compound = 1.0
                for monthly_excess in monthly_excess_list:
                    year_compound *= (1 + monthly_excess / 100)
                yearly_excess = (year_compound - 1) * 100
                yearly_results[f"year{year}"] = round(yearly_excess, 2)
            else:
                yearly_results[f"year{year}"] = None

        # 计算平均超额
        valid_returns = [v for v in yearly_results.values() if v is not None]
        avg_excess = round(sum(valid_returns) / len(valid_returns), 2) if valid_returns else 0

        yearly_results['avgExcess'] = avg_excess

        return yearly_results

    def calculate_period_excess(
        self,
        nav_data: List,
        index_data: List[Dict],
        start_date: str,
        end_date: str,
        fund_code: str = None
    ) -> Dict[str, Any]:
        """
        计算区间超额收益
        使用复权累计净值（adjusted_accum_nav），自动考虑分红影响
        """
        # 转换为DataFrame（使用复权累计净值）
        nav_df = pd.DataFrame([{
            "date": pd.to_datetime(nav.nav_date),
            "nav": float(nav.adjusted_accum_nav) if nav.adjusted_accum_nav else float(nav.unit_nav)
        } for nav in nav_data])

        # DEBUG: 输出使用的净值类型
        if fund_code and len(nav_data) > 0:
            first_nav = nav_data[0]
            has_adjusted = first_nav.adjusted_accum_nav is not None
            print(f"DEBUG [{fund_code}]: 使用净值类型 = {'adjusted_accum_nav' if has_adjusted else 'unit_nav'}, 共{len(nav_data)}条")

        index_df = pd.DataFrame(index_data)
        index_df['date'] = pd.to_datetime(index_df['date'])

        # 按日期排序
        nav_df = nav_df.sort_values('date').reset_index(drop=True)
        index_df = index_df.sort_values('date').reset_index(drop=True)

        # 对齐起始和结束日期
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date)

        start_data = self._align_data_by_date(nav_df, index_df, start_ts, 'backward')
        end_data = self._align_data_by_date(nav_df, index_df, end_ts, 'backward')

        if start_data is None or end_data is None:
            if fund_code:
                print(f"DEBUG [{fund_code}]: 数据对齐失败 - start_data={'None' if start_data is None else 'OK'}, end_data={'None' if end_data is None else 'OK'}")
            return {}

        # DEBUG: 输出期初期末数据
        if fund_code:
            print(f"DEBUG [{fund_code}]: 期初 {start_data['date'].strftime('%Y-%m-%d')} nav={start_data['nav']:.4f}")
            print(f"DEBUG [{fund_code}]: 期末 {end_data['date'].strftime('%Y-%m-%d')} nav={end_data['nav']:.4f}")

        # 使用复权累计净值，直接计算收益，不需要复杂的分红调整
        # 计算产品收益率
        product_return = ((end_data['nav'] / start_data['nav']) - 1) * 100

        # 计算指数收益率
        index_return = ((end_data['index'] / start_data['index']) - 1) * 100

        # 计算超额收益
        excess_return = product_return - index_return

        # DEBUG: 输出计算结果
        if fund_code:
            print(f"DEBUG [{fund_code}]: 产品收益={product_return:.2f}%, 指数收益={index_return:.2f}%, 超额={excess_return:.2f}%")

        # 筛选区间内的数据来计算回撤
        period_nav = nav_df[(nav_df['date'] >= start_data['date']) & (nav_df['date'] <= end_data['date'])]
        period_index = index_df[(index_df['date'] >= start_data['date']) & (index_df['date'] <= end_data['date'])]

        # 合并计算超额曲线
        merged = pd.merge(period_nav, period_index, on='date', how='inner')

        if len(merged) < 2:
            max_drawdown = 0
        else:
            # 使用复权累计净值计算累计收益曲线（不需要分红调整）
            merged['nav_cum_return'] = merged['nav'] / merged['nav'].iloc[0]
            merged['index_cum_return'] = merged['value'] / merged['value'].iloc[0]
            merged['excess'] = (merged['nav_cum_return'] - merged['index_cum_return']) * 100

            # 计算最大回撤
            merged['nav_cummax'] = merged['nav_cum_return'].cummax()
            merged['drawdown'] = (merged['nav_cum_return'] / merged['nav_cummax'] - 1) * 100
            max_drawdown = merged['drawdown'].min()

            # 计算超额曲线
            merged['excess_curve'] = merged['nav_cum_return'] / merged['index_cum_return']

            # 计算超额回撤
            merged['excess_peak'] = merged['excess_curve'].cummax()
            merged['excess_drawdown'] = (1 - merged['excess_curve'] / merged['excess_peak']) * 100

            max_drawdown = merged['excess_drawdown'].max()

        # 计算年化超额
        days = (end_data['date'] - start_data['date']).days
        if days > 0:
            annualized_excess = ((1 + excess_return / 100) ** (252 / days) - 1) * 100
        else:
            annualized_excess = 0

        return {
            "startDate": start_data['date'].strftime("%Y-%m-%d"),
            "endDate": end_data['date'].strftime("%Y-%m-%d"),
            "productReturn": round(product_return, 2),
            "indexReturn": round(index_return, 2),
            "excessReturn": round(excess_return, 2),
            "maxDrawdown": round(max_drawdown, 2),
            "annualizedExcess": round(annualized_excess, 2)
        }

    def calculate_risk_metrics(
        self,
        nav_data: List,
        index_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        计算风险指标
        使用复权累计净值（adjusted_accum_nav），自动考虑分红影响
        """
        # 转换为DataFrame（使用复权累计净值）
        nav_df = pd.DataFrame([{
            "date": pd.to_datetime(nav.nav_date),
            "nav": float(nav.adjusted_accum_nav) if nav.adjusted_accum_nav else float(nav.unit_nav)
        } for nav in nav_data])

        index_df = pd.DataFrame(index_data)
        index_df['date'] = pd.to_datetime(index_df['date'])

        # 合并数据
        merged_df = pd.merge(nav_df, index_df, on='date', how='inner')

        if len(merged_df) < 2:
            return {}

        # 计算日收益率
        merged_df = merged_df.sort_values('date').reset_index(drop=True)
        merged_df['nav_return'] = merged_df['nav'].pct_change()
        merged_df['index_return'] = merged_df['value'].pct_change()
        merged_df['excess_return'] = merged_df['nav_return'] - merged_df['index_return']

        # 删除空值
        merged_df = merged_df.dropna()

        if len(merged_df) == 0:
            return {}

        # 计算年化超额收益
        total_excess = merged_df['excess_return'].sum()
        annualized_excess = total_excess * 252

        # 计算超额波动率
        excess_volatility = merged_df['excess_return'].std() * np.sqrt(252)

        # 计算超额夏普比率
        excess_sharpe = annualized_excess / excess_volatility if excess_volatility > 0 else 0

        # 计算最大超额回撤
        cum_excess = (1 + merged_df['excess_return']).cumprod()
        max_drawdown = (cum_excess / cum_excess.cummax() - 1).min()

        # 计算卡玛比率
        calmar_ratio = annualized_excess / abs(max_drawdown) if max_drawdown != 0 else 0

        # 计算月度胜率
        merged_df['year_month'] = merged_df['date'].dt.to_period('M')
        monthly_excess = merged_df.groupby('year_month')['excess_return'].sum()
        win_rate = (monthly_excess > 0).sum() / len(monthly_excess) * 100 if len(monthly_excess) > 0 else 0

        # 计算跟踪误差
        tracking_error = merged_df['excess_return'].std() * np.sqrt(252)

        # 计算信息比率
        information_ratio = annualized_excess / tracking_error if tracking_error > 0 else 0

        return {
            "annualizedExcess": round(annualized_excess * 100, 2),
            "excessVolatility": round(excess_volatility * 100, 2),
            "excessSharpe": round(excess_sharpe, 2),
            "maxExcessDrawdown": round(max_drawdown * 100, 2),
            "calmarRatio": round(calmar_ratio, 2),
            "winRate": round(win_rate, 1),
            "trackingError": round(tracking_error * 100, 2),
            "informationRatio": round(information_ratio, 2)
        }

    def calculate_weekly_excess_curve(
        self,
        nav_data: List,
        index_data: List[Dict],
        fund_code: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """
        计算周度累计超额曲线数据（考虑分红影响）
        返回格式: [{"date": "2024-01-05", "cumExcessReturn": 1.5}, ...]
        使用复权累计净值（adjusted_accum_nav），自动考虑分红影响
        """
        # 转换为DataFrame（使用复权累计净值）
        nav_df = pd.DataFrame([{
            "date": pd.to_datetime(nav.nav_date),
            "nav": float(nav.adjusted_accum_nav) if nav.adjusted_accum_nav else float(nav.unit_nav)
        } for nav in nav_data])

        index_df = pd.DataFrame(index_data)
        index_df['date'] = pd.to_datetime(index_df['date'])

        # 按日期排序
        nav_df = nav_df.sort_values('date').reset_index(drop=True)
        index_df = index_df.sort_values('date').reset_index(drop=True)

        if len(nav_df) == 0 or len(index_df) == 0:
            return []

        # 确定时间范围
        if start_date:
            date_start = pd.to_datetime(start_date)
        else:
            date_start = nav_df['date'].min()

        if end_date:
            date_end = pd.to_datetime(end_date)
        else:
            date_end = nav_df['date'].max()

        # 筛选时间范围内的净值日期
        period_navs = nav_df[(nav_df['date'] >= date_start) & (nav_df['date'] <= date_end)].copy()

        if len(period_navs) == 0:
            return []

        # 获取所有净值更新日期作为周度数据点
        all_dates = period_navs['date'].tolist()

        # 获取期初数据（第一个日期的前一个交易日）
        first_date = all_dates[0]
        period_start_data = self._align_data_by_date(nav_df, index_df, first_date - pd.Timedelta(days=1), 'backward')

        if period_start_data is None:
            # 如果找不到期初数据，使用第一个点作为起点
            period_start_data = self._align_data_by_date(nav_df, index_df, first_date, 'exact')
            if period_start_data is None:
                return []

        # 计算周度累计超额
        result = []
        compound_factor = 1.0  # 累计倍数
        prev_nav = period_start_data['nav']
        prev_index = period_start_data['index']

        for current_date in all_dates:
            # 获取当前日期数据
            current_data = self._align_data_by_date(nav_df, index_df, current_date, 'exact')

            if current_data is None:
                continue

            # 使用复权累计净值，直接计算周收益率（不需要手动分红调整）
            nav_return = (current_data['nav'] / prev_nav - 1)
            index_return = (current_data['index'] / prev_index - 1)
            weekly_excess = nav_return - index_return

            # 复利累计
            compound_factor *= (1 + weekly_excess)

            # 记录累计超额（百分比）
            cum_excess_pct = (compound_factor - 1) * 100

            result.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "cumExcessReturn": round(cum_excess_pct, 2)
            })

            # 更新为下一周的期初
            prev_nav = current_data['nav']
            prev_index = current_data['index']

        return result
