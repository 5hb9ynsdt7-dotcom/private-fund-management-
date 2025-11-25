"""
基金档期规则解析服务
Fund Schedule Rule Parsing Service
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from calendar import monthrange
import re
import logging

logger = logging.getLogger(__name__)


class FundScheduleService:
    """基金档期规则解析和日期计算服务"""

    def __init__(self):
        pass

    @staticmethod
    def is_trading_day(d: date) -> bool:
        """
        判断是否为交易日（简化版：仅排除周末）
        后续可扩展支持节假日判断
        """
        # 0=Monday, 6=Sunday
        return d.weekday() < 5

    @staticmethod
    def get_last_trading_day_of_month(year: int, month: int) -> date:
        """
        获取指定月份的最后一个交易日
        """
        # 获取该月最后一天
        _, last_day = monthrange(year, month)
        d = date(year, month, last_day)

        # 向前查找最后一个交易日
        while not FundScheduleService.is_trading_day(d):
            d = d - timedelta(days=1)

        return d

    @staticmethod
    def get_trading_day(year: int, month: int, day: int) -> date:
        """
        获取指定日期，如果不是交易日则向后顺延
        """
        try:
            d = date(year, month, day)
        except ValueError:
            # 日期无效（如2月30日），返回该月最后一个交易日
            return FundScheduleService.get_last_trading_day_of_month(year, month)

        # 如果是交易日，直接返回
        if FundScheduleService.is_trading_day(d):
            return d

        # 否则向后顺延到下一个交易日
        while not FundScheduleService.is_trading_day(d):
            d = d + timedelta(days=1)

        return d

    def parse_rule(self, rule_text: str) -> List[str]:
        """
        解析规则文本，提取规则类型

        支持的规则类型：
        - "每月X日"
        - "每月最后一个交易日"
        - "每月最后一天"

        返回规则列表，例如：["day:15", "last_trading_day"]
        """
        if not rule_text:
            return []

        rules = []

        # 匹配"每月X日"或"X日"
        day_pattern = r'每月(\d{1,2})日|(\d{1,2})日'
        for match in re.finditer(day_pattern, rule_text):
            day = match.group(1) or match.group(2)
            rules.append(f"day:{day}")

        # 匹配"每月最后一个交易日"或"月末最后一个交易日"
        if re.search(r'最后一个交易日|月末.*交易日', rule_text):
            rules.append("last_trading_day")

        # 匹配"每月最后一天"或"月末"
        elif re.search(r'每月最后一天|月末', rule_text):
            rules.append("last_day")

        return rules

    def calculate_dates(
        self,
        rule_text: str,
        year: int,
        month: int
    ) -> List[Dict[str, any]]:
        """
        根据规则文本计算指定年月的具体日期

        Args:
            rule_text: 规则文本
            year: 年份
            month: 月份

        Returns:
            日期列表，每个元素包含：
            - date: 日期对象
            - date_str: 日期字符串 (YYYY-MM-DD)
            - display: 显示文本 (MM月DD日)
            - rule_type: 规则类型
        """
        rules = self.parse_rule(rule_text)
        dates = []

        for rule in rules:
            try:
                if rule.startswith("day:"):
                    # 特定日期
                    day = int(rule.split(":")[1])
                    d = self.get_trading_day(year, month, day)
                    dates.append({
                        "date": d,
                        "date_str": d.strftime("%Y-%m-%d"),
                        "display": f"{d.month}月{d.day}日",
                        "rule_type": f"每月{day}日"
                    })

                elif rule == "last_trading_day":
                    # 最后一个交易日
                    d = self.get_last_trading_day_of_month(year, month)
                    dates.append({
                        "date": d,
                        "date_str": d.strftime("%Y-%m-%d"),
                        "display": f"{d.month}月{d.day}日",
                        "rule_type": "最后一个交易日"
                    })

                elif rule == "last_day":
                    # 最后一天
                    _, last_day = monthrange(year, month)
                    d = date(year, month, last_day)
                    dates.append({
                        "date": d,
                        "date_str": d.strftime("%Y-%m-%d"),
                        "display": f"{d.month}月{d.day}日",
                        "rule_type": "最后一天"
                    })

            except Exception as e:
                logger.error(f"计算日期失败: rule={rule}, year={year}, month={month}, error={str(e)}")
                continue

        # 按日期排序并去重
        dates = sorted(dates, key=lambda x: x["date"])
        unique_dates = []
        seen_dates = set()

        for item in dates:
            if item["date_str"] not in seen_dates:
                unique_dates.append(item)
                seen_dates.add(item["date_str"])

        return unique_dates

    def calculate_month_schedule(
        self,
        subscription_rule: str,
        redemption_rule: str,
        year: int,
        month: int
    ) -> Dict[str, any]:
        """
        计算指定月份的完整档期信息

        Returns:
            {
                "year": 年份,
                "month": 月份,
                "subscription_dates": [申购日期列表],
                "redemption_dates": [赎回日期列表]
            }
        """
        return {
            "year": year,
            "month": month,
            "subscription_dates": self.calculate_dates(subscription_rule, year, month),
            "redemption_dates": self.calculate_dates(redemption_rule, year, month)
        }

    def calculate_calendar_data(
        self,
        fund_schedules: List[Dict[str, any]],
        year: int,
        month: int
    ) -> Dict[str, any]:
        """
        计算月历数据，用于前端日历展示

        Args:
            fund_schedules: 基金档期列表，每个元素包含：
                - fund_code: 基金代码
                - fund_name: 基金名称
                - subscription_rule: 申购规则
                - redemption_rule: 赎回规则
                - main_strategy: 大类策略
                - sub_strategy: 细分策略
            year: 年份
            month: 月份

        Returns:
            {
                "year": 年份,
                "month": 月份,
                "calendar_days": {
                    "YYYY-MM-DD": {
                        "subscriptions": [基金列表],
                        "redemptions": [基金列表]
                    }
                }
            }
        """
        calendar_days = {}

        for fund_schedule in fund_schedules:
            fund_code = fund_schedule.get("fund_code")
            fund_name = fund_schedule.get("fund_name")
            subscription_rule = fund_schedule.get("subscription_rule", "")
            redemption_rule = fund_schedule.get("redemption_rule", "")
            main_strategy = fund_schedule.get("main_strategy", "")
            sub_strategy = fund_schedule.get("sub_strategy", "")

            # 计算申购日期
            subscription_dates = self.calculate_dates(subscription_rule, year, month)
            for date_info in subscription_dates:
                date_str = date_info["date_str"]
                if date_str not in calendar_days:
                    calendar_days[date_str] = {
                        "subscriptions": [],
                        "redemptions": []
                    }

                calendar_days[date_str]["subscriptions"].append({
                    "fund_code": fund_code,
                    "fund_name": fund_name,
                    "main_strategy": main_strategy,
                    "sub_strategy": sub_strategy,
                    "rule_type": date_info["rule_type"]
                })

            # 计算赎回日期
            redemption_dates = self.calculate_dates(redemption_rule, year, month)
            for date_info in redemption_dates:
                date_str = date_info["date_str"]
                if date_str not in calendar_days:
                    calendar_days[date_str] = {
                        "subscriptions": [],
                        "redemptions": []
                    }

                calendar_days[date_str]["redemptions"].append({
                    "fund_code": fund_code,
                    "fund_name": fund_name,
                    "main_strategy": main_strategy,
                    "sub_strategy": sub_strategy,
                    "rule_type": date_info["rule_type"]
                })

        return {
            "year": year,
            "month": month,
            "calendar_days": calendar_days
        }
