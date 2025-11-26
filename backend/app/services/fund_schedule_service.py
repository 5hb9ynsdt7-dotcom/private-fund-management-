"""
基金档期规则解析服务
Fund Schedule Rule Parsing Service
"""

from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, date, timedelta
from calendar import monthrange
import re
import logging

logger = logging.getLogger(__name__)


class FundScheduleService:
    """基金档期规则解析和日期计算服务"""

    # 中国大陆法定节假日列表（2024-2025年）
    # 格式：'YYYY-MM-DD'
    HOLIDAYS = {
        # 2024年节假日
        '2024-01-01',  # 元旦
        '2024-02-10', '2024-02-11', '2024-02-12', '2024-02-13',
        '2024-02-14', '2024-02-15', '2024-02-16', '2024-02-17',  # 春节
        '2024-04-04', '2024-04-05', '2024-04-06',  # 清明节
        '2024-05-01', '2024-05-02', '2024-05-03', '2024-05-04', '2024-05-05',  # 劳动节
        '2024-06-10',  # 端午节
        '2024-09-15', '2024-09-16', '2024-09-17',  # 中秋节
        '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04',
        '2024-10-05', '2024-10-06', '2024-10-07',  # 国庆节

        # 2025年节假日
        '2025-01-01',  # 元旦
        '2025-01-28', '2025-01-29', '2025-01-30', '2025-01-31',
        '2025-02-01', '2025-02-02', '2025-02-03', '2025-02-04',  # 春节
        '2025-04-04', '2025-04-05', '2025-04-06',  # 清明节
        '2025-05-01', '2025-05-02', '2025-05-03', '2025-05-04', '2025-05-05',  # 劳动节
        '2025-05-31', '2025-06-01', '2025-06-02',  # 端午节
        '2025-10-01', '2025-10-02', '2025-10-03', '2025-10-04',
        '2025-10-05', '2025-10-06', '2025-10-07', '2025-10-08',  # 国庆节+中秋节（合并放假8天）

        # 2026年节假日（可以继续扩展）
        '2026-01-01', '2026-01-02', '2026-01-03',  # 元旦
        '2026-02-17', '2026-02-18', '2026-02-19', '2026-02-20',
        '2026-02-21', '2026-02-22', '2026-02-23',  # 春节
    }

    def __init__(self):
        pass

    @staticmethod
    def is_trading_day(d: date) -> bool:
        """
        判断是否为交易日
        排除周末和中国大陆法定节假日
        """
        # 周末不是交易日
        if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False

        # 检查是否为法定节假日
        date_str = d.strftime('%Y-%m-%d')
        if date_str in FundScheduleService.HOLIDAYS:
            return False

        return True

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
    def get_trading_day(year: int, month: int, day: int, adjust_forward: bool = True) -> date:
        """
        获取指定日期，如果不是交易日则调整

        Args:
            year: 年份
            month: 月份
            day: 日
            adjust_forward: True表示向后顺延，False表示向前提前
        """
        try:
            d = date(year, month, day)
        except ValueError:
            # 日期无效（如2月30日），返回该月最后一个交易日
            return FundScheduleService.get_last_trading_day_of_month(year, month)

        # 如果是交易日，直接返回
        if FundScheduleService.is_trading_day(d):
            return d

        # 根据参数决定调整方向
        if adjust_forward:
            # 向后顺延到下一个交易日
            while not FundScheduleService.is_trading_day(d):
                d = d + timedelta(days=1)
        else:
            # 向前提前到上一个交易日
            while not FundScheduleService.is_trading_day(d):
                d = d - timedelta(days=1)

        return d

    @staticmethod
    def get_nth_weekday_of_month(year: int, month: int, nth: int, weekday: int) -> Optional[date]:
        """
        获取指定月份的第N个星期X

        Args:
            year: 年份
            month: 月份
            nth: 第几个（1-5）
            weekday: 星期几（0=Monday, 6=Sunday）

        Returns:
            日期对象，如果不存在则返回None
        """
        # 获取该月第一天
        first_day = date(year, month, 1)
        _, last_day_num = monthrange(year, month)

        # 找到该月所有符合条件的星期X
        matching_days = []
        for day in range(1, last_day_num + 1):
            d = date(year, month, day)
            if d.weekday() == weekday:
                matching_days.append(d)

        # 返回第nth个
        if 0 < nth <= len(matching_days):
            return matching_days[nth - 1]

        return None

    @staticmethod
    def parse_weekday_name(weekday_text: str) -> Optional[int]:
        """
        解析中文星期名称为数字

        Args:
            weekday_text: 中文星期名称，如"周一"、"周五"、"星期五"等

        Returns:
            星期数字（0=Monday, 6=Sunday），解析失败返回None
        """
        weekday_map = {
            '一': 0, '1': 0,
            '二': 1, '2': 1,
            '三': 2, '3': 2,
            '四': 3, '4': 3,
            '五': 4, '5': 4,
            '六': 5, '6': 5,
            '日': 6, '天': 6, '7': 6, '0': 6
        }

        # 提取星期数字/名称
        for pattern in [r'周([一二三四五六日天\d])', r'星期([一二三四五六日天\d])']:
            match = re.search(pattern, weekday_text)
            if match:
                day_char = match.group(1)
                return weekday_map.get(day_char)

        return None

    @staticmethod
    def parse_chinese_number(num_text: str) -> Optional[int]:
        """
        解析中文数字为阿拉伯数字

        Args:
            num_text: 中文数字，如"一"、"三"等

        Returns:
            数字，解析失败返回None
        """
        num_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
        }
        return num_map.get(num_text)

    def parse_rule(self, rule_text: str) -> List[Tuple[str, str]]:
        """
        解析规则文本，提取规则类型

        支持的规则类型：
        - "每月X日"
        - "每月最后一个交易日"
        - "每月最后一天"
        - "第X个周Y" (如：第一个周五、第三个周五)
        - "每周Y" (如：每周三、每周五)

        返回规则列表，每个元素为 (规则, 调整策略)
        调整策略：'forward'(顺延), 'backward'(提前), 'skip'(不开放)
        例如：[("day:15", "forward"), ("every_weekday:2", "skip")]
        """
        if not rule_text:
            return []

        rules = []

        # 判断非交易日/节假日的调整策略
        # "提前" 表示向前调整
        # "顺延" 或 "延后" 表示向后调整
        # "不开放" 表示跳过该日期
        # 默认：对于固定日期（每月X日）使用顺延，对于周期规则（每周X）使用不开放
        adjust_mode = None  # 先不设置，根据规则类型决定
        if re.search(r'提前', rule_text):
            adjust_mode = 'backward'
        elif re.search(r'顺延|延后', rule_text):
            adjust_mode = 'forward'
        elif re.search(r'不开放', rule_text):
            adjust_mode = 'skip'

        # 匹配"每周X"、"每个自然周周X" (如：每周三、每周五、每个自然周周四)
        every_weekday_pattern = r'每(?:个自然)?(?:周|星期)(?:周|星期)?([一二三四五六日天\d])'
        for match in re.finditer(every_weekday_pattern, rule_text):
            weekday_text = match.group(1)
            weekday = self.parse_weekday_name(f"周{weekday_text}")

            if weekday is not None:
                # 对于"每周X"规则，如果没有明确指定调整方式，默认为skip（不开放）
                mode = adjust_mode if adjust_mode is not None else 'skip'
                rules.append((f"every_weekday:{weekday}", mode))

        # 匹配"第X个周Y" 或 "每月第X个周Y"
        # 例如：第一个周五、第三个周五、每月第一个周五
        nth_weekday_pattern = r'第([一二三四五1-5])个(?:周|星期)([一二三四五六日天\d])'
        for match in re.finditer(nth_weekday_pattern, rule_text):
            nth_text = match.group(1)
            weekday_text = match.group(2)

            nth = self.parse_chinese_number(nth_text)
            weekday = self.parse_weekday_name(f"周{weekday_text}")

            if nth is not None and weekday is not None:
                # 对于"第X个周Y"规则，如果没有明确指定调整方式，默认为skip（不开放）
                mode = adjust_mode if adjust_mode is not None else 'skip'
                rules.append((f"nth_weekday:{nth}:{weekday}", mode))

        # 匹配"每月X日"、"每月X号"、"每个自然月X日"、"X日"、"X号"
        day_pattern = r'每(?:个自然)?月(\d{1,2})[日号]|(?<![每第]月)(\d{1,2})[日号]'
        for match in re.finditer(day_pattern, rule_text):
            day = match.group(1) or match.group(2)
            if day:  # 确保匹配到了数字
                # 对于"每月X日"规则，如果没有明确指定调整方式，默认为forward（顺延）
                mode = adjust_mode if adjust_mode is not None else 'forward'
                rules.append((f"day:{day}", mode))

        # 匹配"每月最后一个交易日"或"月末最后一个交易日"
        if re.search(r'最后一个交易日|月末.*交易日', rule_text):
            # 最后交易日规则一般不需要调整（本身就是交易日）
            mode = adjust_mode if adjust_mode is not None else 'forward'
            rules.append(("last_trading_day", mode))

        # 匹配"每月最后一天"或"月末"
        elif re.search(r'每月最后一天|月末', rule_text):
            # 最后一天如果是假期，默认顺延
            mode = adjust_mode if adjust_mode is not None else 'forward'
            rules.append(("last_day", mode))

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

        weekday_names = {0: '一', 1: '二', 2: '三', 3: '四', 4: '五', 5: '六', 6: '日'}
        nth_names = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五'}

        for rule, adjust_mode in rules:
            try:
                if rule.startswith("day:"):
                    # 特定日期
                    day = int(rule.split(":")[1])
                    d = self.get_trading_day(year, month, day, adjust_mode != 'backward')

                    # 如果调整模式是skip且原日期不是交易日，则跳过
                    if adjust_mode == 'skip':
                        try:
                            original_date = date(year, month, day)
                            if not self.is_trading_day(original_date):
                                continue
                        except ValueError:
                            continue

                    dates.append({
                        "date": d,
                        "date_str": d.strftime("%Y-%m-%d"),
                        "display": f"{d.month}月{d.day}日",
                        "rule_type": f"每月{day}日"
                    })

                elif rule.startswith("every_weekday:"):
                    # 每周X（找到该月所有符合条件的星期X）
                    weekday = int(rule.split(":")[1])
                    _, last_day_num = monthrange(year, month)

                    # 找到该月所有的周X
                    for day in range(1, last_day_num + 1):
                        d = date(year, month, day)
                        if d.weekday() == weekday:
                            # 检查是否为交易日
                            if not self.is_trading_day(d):
                                if adjust_mode == 'skip':
                                    # 不开放，跳过该日期
                                    continue
                                elif adjust_mode == 'forward':
                                    # 向后顺延
                                    while not self.is_trading_day(d):
                                        d = d + timedelta(days=1)
                                elif adjust_mode == 'backward':
                                    # 向前提前
                                    while not self.is_trading_day(d):
                                        d = d - timedelta(days=1)

                            rule_type = f"每周{weekday_names.get(weekday, str(weekday))}"
                            dates.append({
                                "date": d,
                                "date_str": d.strftime("%Y-%m-%d"),
                                "display": f"{d.month}月{d.day}日",
                                "rule_type": rule_type
                            })

                elif rule.startswith("nth_weekday:"):
                    # 第N个星期X
                    parts = rule.split(":")
                    nth = int(parts[1])
                    weekday = int(parts[2])

                    # 计算第nth个weekday
                    d = self.get_nth_weekday_of_month(year, month, nth, weekday)
                    if d is None:
                        continue

                    # 检查是否为交易日，如果不是则根据调整模式处理
                    if not self.is_trading_day(d):
                        if adjust_mode == 'skip':
                            # 不开放，跳过该日期
                            continue
                        elif adjust_mode == 'forward':
                            # 向后顺延
                            while not self.is_trading_day(d):
                                d = d + timedelta(days=1)
                        elif adjust_mode == 'backward':
                            # 向前提前
                            while not self.is_trading_day(d):
                                d = d - timedelta(days=1)

                    rule_type = f"第{nth_names.get(nth, str(nth))}个周{weekday_names.get(weekday, str(weekday))}"
                    dates.append({
                        "date": d,
                        "date_str": d.strftime("%Y-%m-%d"),
                        "display": f"{d.month}月{d.day}日",
                        "rule_type": rule_type
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
