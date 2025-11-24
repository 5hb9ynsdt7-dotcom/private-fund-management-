"""
诺亚CRM净值抓取服务
Noah CRM NAV Crawler Service
"""

import requests
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from decimal import Decimal

from ..models import Fund, Nav
from ..data.noah_product_mapping import get_noah_product_id, get_all_mapped_funds

logger = logging.getLogger(__name__)


class NoahCRMCrawler:
    """诺亚CRM系统爬虫"""

    BASE_URL = "https://crm.noah-fund.com"
    LOGIN_URL = f"{BASE_URL}/auth/login"  # 需要确认实际登录API
    NET_VALUE_URL = f"{BASE_URL}/nbp/api/product/v1/net_value_chart_query"
    CAPTCHA_URL = f"{BASE_URL}/auth/captcha"  # 需要确认实际验证码API

    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.nfp_token = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': '*/*',
            'nbp-app-name': 'zx_crm_pc',
            'region': 'DOMESTIC',
            'channel': 'zx',
            'client': 'pc',
            'roleType': 'Team_AR',
            'app-name': 'nfpp',
        }

    def set_tokens(self, access_token: str, nfp_token: str, fc_code: str = "18814"):
        """
        设置认证令牌
        从用户登录后手动提供
        """
        # 清理token，移除所有空白字符（空格、换行、制表符等）
        access_token = ''.join(access_token.split())
        nfp_token = ''.join(nfp_token.split())

        self.access_token = access_token
        self.nfp_token = nfp_token
        self.headers.update({
            'access-token': access_token,
            'nfp-token': nfp_token,
            'fcCode': fc_code,
        })
        logger.info("认证令牌已设置")

    def get_captcha(self) -> Tuple[bytes, str]:
        """
        获取登录验证码
        返回: (验证码图片字节流, 验证码key)
        """
        try:
            response = self.session.get(
                self.CAPTCHA_URL,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            # 从响应头获取验证码key
            captcha_key = response.headers.get('captcha-key', '')
            captcha_image = response.content

            logger.info("验证码获取成功")
            return captcha_image, captcha_key

        except Exception as e:
            logger.error(f"获取验证码失败: {str(e)}")
            raise

    def login(self, username: str, password: str, captcha: str, captcha_key: str) -> Dict:
        """
        登录诺亚CRM系统

        参数:
            username: 用户名
            password: 密码
            captcha: 验证码
            captcha_key: 验证码key

        返回:
            登录结果包含token信息
        """
        try:
            payload = {
                "username": username,
                "password": password,
                "captcha": captcha,
                "captchaKey": captcha_key
            }

            response = self.session.post(
                self.LOGIN_URL,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            if result.get('code') == '0' or result.get('success'):
                # 提取token
                data = result.get('response') or result.get('data')
                self.access_token = data.get('access_token') or data.get('accessToken')
                self.nfp_token = data.get('nfp_token') or data.get('nfpToken')
                fc_code = data.get('fcCode', '18814')

                # 更新headers
                self.set_tokens(self.access_token, self.nfp_token, fc_code)

                logger.info(f"用户 {username} 登录成功")
                return {
                    'success': True,
                    'message': '登录成功',
                    'access_token': self.access_token,
                    'nfp_token': self.nfp_token
                }
            else:
                error_msg = result.get('message') or result.get('subMessage') or '登录失败'
                logger.error(f"登录失败: {error_msg}")
                return {
                    'success': False,
                    'message': error_msg
                }

        except Exception as e:
            logger.error(f"登录过程出错: {str(e)}")
            return {
                'success': False,
                'message': f'登录出错: {str(e)}'
            }

    def fetch_nav_data(self, product_id: str, nav_type: str = "1") -> Dict:
        """
        抓取单个产品的净值数据

        参数:
            product_id: 诺亚CRM产品ID
            nav_type: "1"=单位净值, "2"=累计净值

        返回:
            净值数据列表
        """
        try:
            payload = {
                "duringDate": "0",  # 全部时间
                "shareCatId": "",
                "batchId": "",
                "productId": product_id,
                "type": nav_type
            }

            response = self.session.post(
                self.NET_VALUE_URL,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if result.get('code') == '0':
                response_data = result.get('response', {})
                range_data_list = response_data.get('rangeDataList', [])

                if range_data_list:
                    nav_list = range_data_list[0].get('netValueList', [])
                    logger.info(f"产品 {product_id} 获取到 {len(nav_list)} 条净值记录")
                    return {
                        'success': True,
                        'data': nav_list
                    }
                else:
                    return {
                        'success': False,
                        'message': '没有净值数据'
                    }
            else:
                error_msg = result.get('message', '获取净值失败')
                logger.error(f"获取净值失败: {error_msg}")
                return {
                    'success': False,
                    'message': error_msg
                }

        except Exception as e:
            logger.error(f"抓取净值数据出错: {str(e)}")
            return {
                'success': False,
                'message': f'抓取出错: {str(e)}'
            }

    def fetch_fund_nav(self, fund_code: str, product_id: Optional[str] = None) -> Dict:
        """
        抓取指定基金的单位净值和累计净值

        参数:
            fund_code: 基金代码，如L03100
            product_id: 诺亚产品ID（可选，如果提供则直接使用）

        返回:
            包含单位净值和累计净值的数据
        """
        # 如果没有提供product_id，尝试从配置文件中读取
        if not product_id:
            product_id = get_noah_product_id(fund_code)

        if not product_id:
            return {
                'success': False,
                'message': f'基金 {fund_code} 未配置诺亚CRM产品ID映射'
            }

        # 获取单位净值
        unit_nav_result = self.fetch_nav_data(product_id, nav_type="1")
        if not unit_nav_result['success']:
            return unit_nav_result

        # 获取累计净值
        accum_nav_result = self.fetch_nav_data(product_id, nav_type="2")
        if not accum_nav_result['success']:
            return accum_nav_result

        # 合并数据
        unit_navs = {item['date']: item['netvalue'] for item in unit_nav_result['data']}
        accum_navs = {item['date']: item['netvalue'] for item in accum_nav_result['data']}

        # 组合数据
        combined_data = []
        for nav_date in unit_navs.keys():
            if nav_date in accum_navs:
                combined_data.append({
                    'date': nav_date,
                    'unit_nav': unit_navs[nav_date],
                    'accum_nav': accum_navs[nav_date]
                })

        return {
            'success': True,
            'fund_code': fund_code,
            'data': combined_data
        }


class NavCrawlerService:
    """净值抓取服务"""

    def __init__(self, db: Session):
        self.db = db
        self.crawler = NoahCRMCrawler()

    def set_crawler_tokens(self, access_token: str, nfp_token: str, fc_code: str = "18814"):
        """设置爬虫认证令牌"""
        self.crawler.set_tokens(access_token, nfp_token, fc_code)

    def login_noah_crm(self, username: str, password: str, captcha: str, captcha_key: str) -> Dict:
        """登录诺亚CRM"""
        return self.crawler.login(username, password, captcha, captcha_key)

    def crawl_and_save_nav(self, fund_code: str) -> Dict:
        """
        抓取并保存单个基金的净值数据

        参数:
            fund_code: 基金代码

        返回:
            处理结果统计
        """
        # 检查基金是否存在
        fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
        if not fund:
            return {
                'success': False,
                'fund_code': fund_code,
                'message': f'基金 {fund_code} 不存在'
            }

        # 优先从数据库获取product_id
        product_id = fund.noah_product_id if fund.noah_product_id else None

        # 抓取净值数据
        crawl_result = self.crawler.fetch_fund_nav(fund_code, product_id=product_id)
        if not crawl_result['success']:
            return crawl_result

        nav_data = crawl_result['data']

        # 保存到数据库
        success_count = 0
        failed_count = 0
        updated_count = 0
        created_count = 0
        errors = []

        for item in nav_data:
            try:
                nav_date = datetime.strptime(item['date'], '%Y-%m-%d').date()
                unit_nav = Decimal(str(item['unit_nav']))
                accum_nav = Decimal(str(item['accum_nav']))

                # 检查是否已存在
                existing_nav = self.db.query(Nav).filter(
                    Nav.fund_code == fund_code,
                    Nav.nav_date == nav_date
                ).first()

                if existing_nav:
                    # 更新
                    existing_nav.unit_nav = unit_nav
                    existing_nav.accum_nav = accum_nav
                    updated_count += 1
                else:
                    # 创建新记录
                    new_nav = Nav(
                        fund_code=fund_code,
                        nav_date=nav_date,
                        unit_nav=unit_nav,
                        accum_nav=accum_nav
                    )
                    self.db.add(new_nav)
                    created_count += 1

                success_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(f"日期 {item.get('date')}: {str(e)}")
                logger.error(f"保存净值记录失败: {str(e)}")

        try:
            self.db.commit()
            logger.info(f"基金 {fund_code} 净值保存成功: 新增{created_count}, 更新{updated_count}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"数据库提交失败: {str(e)}")
            return {
                'success': False,
                'fund_code': fund_code,
                'message': f'数据库保存失败: {str(e)}'
            }

        return {
            'success': True,
            'fund_code': fund_code,
            'fund_name': fund.fund_name,
            'success_count': success_count,
            'failed_count': failed_count,
            'created_count': created_count,
            'updated_count': updated_count,
            'errors': errors
        }

    def crawl_all_funds(self, fund_codes: Optional[List[str]] = None) -> Dict:
        """
        批量抓取多个基金的净值

        参数:
            fund_codes: 基金代码列表，如果为None则抓取所有已配置映射的基金

        返回:
            批量处理结果统计
        """
        if fund_codes is None:
            # 优先从数据库中获取已配置映射的基金
            from ..models import Fund
            db_funds = self.db.query(Fund).filter(Fund.noah_product_id.isnot(None), Fund.noah_product_id != '').all()
            fund_codes = [fund.fund_code for fund in db_funds]

            # 如果数据库中没有，尝试从配置文件中读取（向后兼容）
            if not fund_codes:
                fund_codes = get_all_mapped_funds()

        total_success = 0
        total_failed = 0
        total_created = 0
        total_updated = 0
        results = []

        for fund_code in fund_codes:
            result = self.crawl_and_save_nav(fund_code)
            results.append(result)

            if result['success']:
                total_success += result['success_count']
                total_created += result['created_count']
                total_updated += result['updated_count']
                total_failed += result['failed_count']

        return {
            'success': True,
            'total_funds': len(fund_codes),
            'total_success': total_success,
            'total_failed': total_failed,
            'total_created': total_created,
            'total_updated': total_updated,
            'results': results
        }

    def update_fund_noah_product_ids(self):
        """
        批量更新基金表中的诺亚产品ID映射
        """
        from ..data.noah_product_mapping import NOAH_PRODUCT_MAPPING

        updated_count = 0
        for fund_code, product_id in NOAH_PRODUCT_MAPPING.items():
            fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
            if fund:
                fund.noah_product_id = product_id
                updated_count += 1

        try:
            self.db.commit()
            logger.info(f"成功更新 {updated_count} 个基金的诺亚产品ID映射")
            return {
                'success': True,
                'updated_count': updated_count
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新产品ID映射失败: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
