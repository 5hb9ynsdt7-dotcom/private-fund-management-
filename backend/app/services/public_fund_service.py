"""
公募基金服务层
Public Fund Service Layer

提供公募基金管理和分析的业务逻辑
"""

import pandas as pd
import numpy as np
import logging
import json
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from datetime import date, datetime
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc, asc, or_

from ..models_public_fund import PublicFund, PublicFundNav, PublicFundAnalysis
from ..schemas.public_fund import (
    PublicFundCreate, PublicFundUpdate,
    PublicFundNavCreate, PublicFundNavUploadResponse
)

logger = logging.getLogger(__name__)


class PublicFundService:
    """公募基金服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ========== 基金主数据管理 ==========

    def get_fund_list(self,
                      keyword: Optional[str] = None,
                      fund_type: Optional[str] = None,
                      fund_company: Optional[str] = None,
                      is_active: bool = True,
                      page: int = 1,
                      page_size: int = 20) -> Tuple[List[PublicFund], int]:
        """
        获取基金列表（带分页和筛选）
        返回: (基金列表, 总记录数)
        """
        try:
            query = self.db.query(PublicFund)

            # 应用筛选条件
            if keyword:
                query = query.filter(
                    or_(
                        PublicFund.fund_code.like(f"%{keyword}%"),
                        PublicFund.fund_name.like(f"%{keyword}%")
                    )
                )
            if fund_type:
                query = query.filter(PublicFund.fund_type == fund_type)
            if fund_company:
                query = query.filter(PublicFund.fund_company.like(f"%{fund_company}%"))
            if is_active:
                query = query.filter(PublicFund.is_active == True)

            # 获取总数
            total = query.count()

            # 应用排序和分页
            funds = query.order_by(desc(PublicFund.created_at))\
                         .offset((page - 1) * page_size)\
                         .limit(page_size)\
                         .all()

            # 为每个基金添加最新净值日期
            for fund in funds:
                latest_nav = self.db.query(PublicFundNav)\
                    .filter(PublicFundNav.fund_code == fund.fund_code)\
                    .order_by(desc(PublicFundNav.nav_date))\
                    .first()
                fund.latest_nav_date = latest_nav.nav_date if latest_nav else None

            return funds, total

        except Exception as e:
            logger.error(f"获取基金列表失败: {str(e)}")
            raise

    def get_fund_by_code(self, fund_code: str) -> Optional[PublicFund]:
        """根据基金代码获取基金信息"""
        try:
            return self.db.query(PublicFund)\
                          .filter(PublicFund.fund_code == fund_code)\
                          .first()
        except Exception as e:
            logger.error(f"获取基金信息失败: {str(e)}")
            raise

    def create_fund(self, fund_data: PublicFundCreate) -> PublicFund:
        """创建基金记录"""
        try:
            # 检查基金代码是否已存在
            existing = self.get_fund_by_code(fund_data.fund_code)
            if existing:
                raise ValueError(f"基金代码 {fund_data.fund_code} 已存在")

            # 创建新基金
            new_fund = PublicFund(**fund_data.dict())
            self.db.add(new_fund)
            self.db.commit()
            self.db.refresh(new_fund)

            logger.info(f"创建基金成功: {fund_data.fund_code} - {fund_data.fund_name}")
            return new_fund

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建基金失败: {str(e)}")
            raise

    def update_fund(self, fund_code: str, fund_data: PublicFundUpdate) -> PublicFund:
        """更新基金信息"""
        try:
            fund = self.get_fund_by_code(fund_code)
            if not fund:
                raise ValueError(f"基金代码 {fund_code} 不存在")

            # 更新字段
            update_data = fund_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(fund, key, value)

            self.db.commit()
            self.db.refresh(fund)

            logger.info(f"更新基金成功: {fund_code}")
            return fund

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新基金失败: {str(e)}")
            raise

    def delete_fund(self, fund_code: str) -> bool:
        """软删除基金（设置is_active=False）"""
        try:
            fund = self.get_fund_by_code(fund_code)
            if not fund:
                raise ValueError(f"基金代码 {fund_code} 不存在")

            fund.is_active = False
            self.db.commit()

            logger.info(f"删除基金成功: {fund_code}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除基金失败: {str(e)}")
            raise

    def fetch_fund_from_eastmoney(self, fund_code: str) -> PublicFund:
        """
        从天天基金网自动抓取基金信息并创建记录
        """
        try:
            import requests
            import re
            from datetime import datetime

            # 获取基金详细数据
            url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://fund.eastmoney.com/'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                raise ValueError(f"抓取失败：HTTP {response.status_code}")

            content = response.text

            # 解析基金基本信息
            fund_name = re.search(r'var fS_name = "(.*?)";', content)
            fund_code_check = re.search(r'var fS_code = "(.*?)";', content)

            if not fund_name or not fund_code_check:
                raise ValueError(f"基金代码 {fund_code} 不存在或数据格式错误")

            # 创建基金记录
            fund_data = PublicFundCreate(
                fund_code=fund_code,
                fund_name=fund_name.group(1),
                fund_type="混合型",  # 默认类型，后续可从其他接口获取
                data_source="eastmoney"
            )

            fund = self.create_fund(fund_data)

            # 抓取并保存净值数据
            self._fetch_and_save_nav_data(fund_code, content)

            return fund

        except requests.RequestException as e:
            logger.error(f"网络请求失败: {str(e)}")
            raise ValueError(f"抓取基金数据失败：网络错误")
        except Exception as e:
            logger.error(f"自动抓取基金失败: {str(e)}")
            raise

    def _fetch_and_save_nav_data(self, fund_code: str, content: str):
        """
        从抓取的内容中提取并保存净值数据
        """
        try:
            import re
            import json
            from datetime import datetime

            # 提取净值走势数据
            nav_trend_match = re.search(r'var Data_netWorthTrend = (\[.*?\]);', content, re.DOTALL)

            if not nav_trend_match:
                logger.warning(f"基金 {fund_code} 没有找到净值数据")
                return

            nav_data_str = nav_trend_match.group(1)
            nav_data_list = json.loads(nav_data_str)

            # 批量保存净值数据
            saved_count = 0
            for nav_point in nav_data_list:
                # x是时间戳（毫秒），y是净值
                timestamp_ms = nav_point.get('x')
                unit_nav = nav_point.get('y')

                if timestamp_ms and unit_nav:
                    # 转换时间戳为日期
                    nav_date = datetime.fromtimestamp(timestamp_ms / 1000).date()

                    # 累计净值使用单位净值（如果没有单独的累计净值数据）
                    accum_nav = unit_nav

                    # 创建净值记录
                    nav_create = PublicFundNavCreate(
                        fund_code=fund_code,
                        nav_date=nav_date,
                        unit_nav=float(unit_nav),
                        accum_nav=float(accum_nav),
                        data_source="eastmoney"
                    )

                    # 使用create_or_update避免重复
                    self.create_or_update_nav(nav_create)
                    saved_count += 1

            self.db.commit()
            logger.info(f"成功保存 {saved_count} 条净值数据")

        except Exception as e:
            logger.error(f"保存净值数据失败: {str(e)}")
            self.db.rollback()
            # 不抛出异常，允许基金创建成功即使净值保存失败

    def refresh_fund_nav(self, fund_code: str) -> dict:
        """
        刷新基金的最新净值数据
        从天天基金网抓取最新净值并更新数据库
        """
        try:
            import requests
            import re
            import json
            from datetime import datetime

            # 获取基金净值数据
            url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://fund.eastmoney.com/'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                raise ValueError(f"抓取失败：HTTP {response.status_code}")

            content = response.text

            # 提取净值走势数据
            nav_trend_match = re.search(r'var Data_netWorthTrend = (\[.*?\]);', content, re.DOTALL)

            if not nav_trend_match:
                return {
                    'success': False,
                    'message': f"基金 {fund_code} 没有找到净值数据"
                }

            nav_data_str = nav_trend_match.group(1)
            nav_data_list = json.loads(nav_data_str)

            if not nav_data_list:
                return {
                    'success': False,
                    'message': f"基金 {fund_code} 净值数据为空"
                }

            # 只保存最新的5条净值数据（避免重复保存大量历史数据）
            recent_navs = nav_data_list[-5:] if len(nav_data_list) > 5 else nav_data_list
            saved_count = 0

            for nav_point in recent_navs:
                timestamp_ms = nav_point.get('x')
                unit_nav = nav_point.get('y')

                if timestamp_ms and unit_nav:
                    nav_date = datetime.fromtimestamp(timestamp_ms / 1000).date()
                    accum_nav = unit_nav

                    nav_create = PublicFundNavCreate(
                        fund_code=fund_code,
                        nav_date=nav_date,
                        unit_nav=float(unit_nav),
                        accum_nav=float(accum_nav),
                        data_source="eastmoney"
                    )

                    self.create_or_update_nav(nav_create)
                    saved_count += 1

            self.db.commit()

            # 获取最新净值信息
            latest_nav = nav_data_list[-1]
            latest_date = datetime.fromtimestamp(latest_nav['x'] / 1000).date()
            latest_value = latest_nav['y']

            logger.info(f"基金 {fund_code} 刷新成功，最新净值：{latest_value} ({latest_date})")

            return {
                'success': True,
                'message': f'净值已更新到最新（{latest_date}：{latest_value}）',
                'latest_date': str(latest_date),
                'latest_nav': float(latest_value),
                'updated_count': saved_count
            }

        except requests.RequestException as e:
            logger.error(f"网络请求失败: {str(e)}")
            return {
                'success': False,
                'message': '抓取失败：网络错误'
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"刷新净值失败: {str(e)}")
            return {
                'success': False,
                'message': f'刷新失败：{str(e)}'
            }

    # ========== 净值数据管理 ==========

    def create_or_update_nav(self, nav_data: PublicFundNavCreate) -> Tuple[PublicFundNav, bool]:
        """
        创建或更新净值记录
        返回: (净值记录, 是否为新创建)
        """
        try:
            # 验证基金是否存在
            fund = self.get_fund_by_code(nav_data.fund_code)
            if not fund:
                raise ValueError(f"基金代码 {nav_data.fund_code} 不存在，请先创建基金")

            # 查找是否已存在相同记录
            existing_nav = self.db.query(PublicFundNav).filter(
                and_(
                    PublicFundNav.fund_code == nav_data.fund_code,
                    PublicFundNav.nav_date == nav_data.nav_date
                )
            ).first()

            if existing_nav:
                # 更新现有记录
                existing_nav.unit_nav = nav_data.unit_nav
                existing_nav.accum_nav = nav_data.accum_nav
                existing_nav.data_source = nav_data.data_source
                self.db.commit()
                self.db.refresh(existing_nav)
                logger.info(f"更新净值记录: {nav_data.fund_code} - {nav_data.nav_date}")
                return existing_nav, False
            else:
                # 创建新记录
                new_nav = PublicFundNav(**nav_data.dict())
                self.db.add(new_nav)
                self.db.commit()
                self.db.refresh(new_nav)
                logger.info(f"创建净值记录: {nav_data.fund_code} - {nav_data.nav_date}")
                return new_nav, True

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建/更新净值记录失败: {str(e)}")
            raise

    def get_nav_list(self,
                     fund_code: str,
                     start_date: Optional[date] = None,
                     end_date: Optional[date] = None,
                     sort_order: str = "desc") -> List[PublicFundNav]:
        """获取净值列表"""
        try:
            query = self.db.query(PublicFundNav).filter(PublicFundNav.fund_code == fund_code)

            # 应用日期筛选
            if start_date:
                query = query.filter(PublicFundNav.nav_date >= start_date)
            if end_date:
                query = query.filter(PublicFundNav.nav_date <= end_date)

            # 应用排序
            if sort_order.lower() == "asc":
                query = query.order_by(asc(PublicFundNav.nav_date))
            else:
                query = query.order_by(desc(PublicFundNav.nav_date))

            return query.all()

        except Exception as e:
            logger.error(f"获取净值列表失败: {str(e)}")
            raise

    def delete_nav_records(self, nav_ids: List[int]) -> Tuple[int, List[str]]:
        """
        删除净值记录
        返回: (删除数量, 错误列表)
        """
        deleted_count = 0
        errors = []

        try:
            for nav_id in nav_ids:
                nav_record = self.db.query(PublicFundNav).filter(PublicFundNav.id == nav_id).first()
                if nav_record:
                    self.db.delete(nav_record)
                    deleted_count += 1
                    logger.info(f"删除净值记录: ID={nav_id}")
                else:
                    errors.append(f"净值记录 ID={nav_id} 不存在")

            self.db.commit()
            return deleted_count, errors

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除净值记录失败: {str(e)}")
            raise

    def process_excel_upload(self, file_content: bytes, filename: str) -> PublicFundNavUploadResponse:
        """
        处理Excel文件上传
        返回处理结果统计
        """
        logger.info(f"开始处理Excel文件: {filename}")

        success_count = 0
        failed_count = 0
        updated_count = 0
        created_count = 0
        errors = []

        try:
            # 读取Excel文件
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')

            # 定义中英文字段映射
            column_mapping = {
                '基金代码': 'fund_code',
                '净值日期': 'nav_date',
                '单位净值': 'unit_nav',
                '累计净值': 'accum_nav',
                'fund_code': 'fund_code',
                'nav_date': 'nav_date',
                'unit_nav': 'unit_nav',
                'accum_nav': 'accum_nav'
            }

            # 转换列名
            df_columns_mapped = {}
            for col in df.columns:
                col_str = str(col).strip()
                if col_str in column_mapping:
                    df_columns_mapped[col] = column_mapping[col_str]
                else:
                    df_columns_mapped[col] = col_str

            df = df.rename(columns=df_columns_mapped)

            logger.info(f"Excel文件列名: {list(df.columns)}")

            # 验证必要列
            required_columns = ['fund_code', 'nav_date', 'unit_nav', 'accum_nav']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                error_msg = f"Excel文件缺少必要列: {', '.join(missing_columns)}"
                errors.append(error_msg)
                return PublicFundNavUploadResponse(
                    success_count=0,
                    failed_count=len(df) if len(df) > 0 else 1,
                    updated_count=0,
                    created_count=0,
                    errors=errors
                )

            # 逐行处理数据
            for index, row in df.iterrows():
                try:
                    fund_code = str(row['fund_code']).strip() if pd.notna(row['fund_code']) else None
                    nav_date_str = str(row['nav_date']).strip() if pd.notna(row['nav_date']) else None
                    unit_nav = float(row['unit_nav']) if pd.notna(row['unit_nav']) else None
                    accum_nav = float(row['accum_nav']) if pd.notna(row['accum_nav']) else None

                    # 数据验证
                    if not fund_code:
                        errors.append(f"第{index+2}行：基金代码不能为空")
                        failed_count += 1
                        continue

                    if not nav_date_str:
                        errors.append(f"第{index+2}行：净值日期不能为空")
                        failed_count += 1
                        continue

                    if unit_nav is None or unit_nav <= 0:
                        errors.append(f"第{index+2}行：单位净值必须大于0")
                        failed_count += 1
                        continue

                    if accum_nav is None or accum_nav < unit_nav:
                        errors.append(f"第{index+2}行：累计净值必须大于等于单位净值")
                        failed_count += 1
                        continue

                    # 创建NavCreate对象
                    nav_data = PublicFundNavCreate(
                        fund_code=fund_code,
                        nav_date=nav_date_str,
                        unit_nav=Decimal(str(unit_nav)),
                        accum_nav=Decimal(str(accum_nav)),
                        data_source='excel'
                    )

                    # 创建或更新净值记录
                    _, is_created = self.create_or_update_nav(nav_data)

                    success_count += 1
                    if is_created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception as e:
                    error_msg = f"第{index+2}行处理失败: {str(e)}"
                    errors.append(error_msg)
                    failed_count += 1
                    logger.warning(error_msg)

            logger.info(f"Excel文件处理完成: 成功{success_count}, 失败{failed_count}")

            return PublicFundNavUploadResponse(
                success_count=success_count,
                failed_count=failed_count,
                updated_count=updated_count,
                created_count=created_count,
                errors=errors
            )

        except Exception as e:
            error_msg = f"Excel文件处理异常: {str(e)}"
            logger.error(error_msg)
            return PublicFundNavUploadResponse(
                success_count=0,
                failed_count=0,
                updated_count=0,
                created_count=0,
                errors=[error_msg]
            )

    def calculate_daily_returns(self, fund_code: str) -> int:
        """
        计算并更新日收益率
        返回: 更新的记录数
        """
        try:
            nav_list = self.get_nav_list(fund_code, sort_order="asc")

            if len(nav_list) < 2:
                return 0

            updated_count = 0
            for i in range(1, len(nav_list)):
                prev_nav = float(nav_list[i-1].unit_nav)
                curr_nav = float(nav_list[i].unit_nav)
                daily_return = ((curr_nav - prev_nav) / prev_nav) * 100 if prev_nav > 0 else 0

                nav_list[i].daily_return = Decimal(str(round(daily_return, 6)))
                updated_count += 1

            self.db.commit()
            logger.info(f"计算日收益率完成: {fund_code}, 更新{updated_count}条记录")
            return updated_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"计算日收益率失败: {str(e)}")
            raise

    # ========== 投研分析（第一阶段：基础框架） ==========

    def calculate_fund_indicators(self,
                                   fund_code: str,
                                   start_date: date,
                                   end_date: date) -> Dict:
        """
        计算单基金的投研指标
        （第一阶段：返回基础统计，后续完善复杂计算）
        """
        try:
            nav_list = self.get_nav_list(fund_code, start_date, end_date, sort_order="asc")

            if len(nav_list) < 2:
                raise ValueError("数据不足，无法计算指标")

            # 转换为DataFrame
            df = pd.DataFrame([{
                'nav_date': nav.nav_date,
                'unit_nav': float(nav.unit_nav),
                'accum_nav': float(nav.accum_nav)
            } for nav in nav_list])

            # 基础计算
            first_nav = df.iloc[0]['accum_nav']
            last_nav = df.iloc[-1]['accum_nav']
            days = (df.iloc[-1]['nav_date'] - df.iloc[0]['nav_date']).days

            # 总收益率
            total_return = ((last_nav - first_nav) / first_nav * 100) if first_nav > 0 else 0

            # 年化收益率
            years = days / 365.0
            annual_return = ((last_nav / first_nav) ** (1 / years) - 1) * 100 if years > 0 and first_nav > 0 else 0

            # 波动率（简化版）
            df['daily_return'] = df['accum_nav'].pct_change() * 100
            volatility = df['daily_return'].std() * np.sqrt(252) if len(df) > 1 else 0

            # 最大回撤
            df['cummax'] = df['accum_nav'].cummax()
            df['drawdown'] = (df['accum_nav'] / df['cummax'] - 1) * 100
            max_drawdown = df['drawdown'].min()

            # 夏普比率（简化版，假设无风险利率3%）
            risk_free_rate = 3.0
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0

            # 卡玛比率
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0

            # 胜率
            positive_days = (df['daily_return'] > 0).sum()
            total_days = (df['daily_return'].notna()).sum()
            win_rate = (positive_days / total_days * 100) if total_days > 0 else 0

            return {
                "total_return": round(total_return, 2),
                "annual_return": round(annual_return, 2),
                "volatility": round(volatility, 2),
                "max_drawdown": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "calmar_ratio": round(calmar_ratio, 2),
                "win_rate": round(win_rate, 2)
            }

        except Exception as e:
            logger.error(f"计算基金指标失败: {str(e)}")
            raise

    # ========== 分析结果存储 ==========

    def save_analysis_result(self,
                             analysis_type: str,
                             analysis_name: str,
                             fund_codes: List[str],
                             analysis_params: Dict,
                             analysis_result: Dict,
                             created_by: Optional[str] = None) -> PublicFundAnalysis:
        """保存分析结果"""
        try:
            new_analysis = PublicFundAnalysis(
                analysis_type=analysis_type,
                analysis_name=analysis_name,
                fund_codes=json.dumps(fund_codes, ensure_ascii=False),
                analysis_params=json.dumps(analysis_params, ensure_ascii=False),
                analysis_result=json.dumps(analysis_result, ensure_ascii=False),
                created_by=created_by
            )
            self.db.add(new_analysis)
            self.db.commit()
            self.db.refresh(new_analysis)

            logger.info(f"保存分析结果成功: {analysis_name}")
            return new_analysis

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存分析结果失败: {str(e)}")
            raise
