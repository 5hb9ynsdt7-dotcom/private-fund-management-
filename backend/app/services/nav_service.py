"""
净值管理服务
Nav Management Service
"""

import pandas as pd
import logging
from typing import List, Dict, Tuple, Optional, Union
from decimal import Decimal
from datetime import date
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, desc, asc

from ..models import Nav, Fund, DateConverter
from ..schemas.nav import NavManualCreate, NavUploadResponse

logger = logging.getLogger(__name__)


class NavService:
    """净值管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_or_update_nav(self, nav_data: NavManualCreate) -> Tuple[Nav, bool]:
        """
        创建或更新净值记录
        返回: (净值记录, 是否为新创建)
        """
        try:
            # 转换日期格式
            if isinstance(nav_data.nav_date, str):
                nav_date = DateConverter.convert_date_string(nav_data.nav_date)
            else:
                nav_date = nav_data.nav_date
            
            # 验证基金是否存在，如果不存在则创建
            fund = self.db.query(Fund).filter(Fund.fund_code == nav_data.fund_code).first()
            if not fund:
                # 自动创建基金记录
                fund_name = getattr(nav_data, 'fund_name', None) or f"基金{nav_data.fund_code}"
                fund = Fund(
                    fund_code=nav_data.fund_code,
                    fund_name=fund_name
                )
                self.db.add(fund)
                self.db.flush()  # 确保基金记录立即可用
                logger.info(f"自动创建基金: {nav_data.fund_code} - {fund_name}")
            
            # 查找是否已存在相同记录
            existing_nav = self.db.query(Nav).filter(
                and_(
                    Nav.fund_code == nav_data.fund_code,
                    Nav.nav_date == nav_date
                )
            ).first()
            
            if existing_nav:
                # 更新现有记录
                existing_nav.unit_nav = nav_data.unit_nav
                existing_nav.accum_nav = nav_data.accum_nav
                self.db.commit()
                logger.info(f"更新净值记录: {nav_data.fund_code} - {nav_date}")
                return existing_nav, False
            else:
                # 创建新记录
                new_nav = Nav(
                    fund_code=nav_data.fund_code,
                    nav_date=nav_date,
                    unit_nav=nav_data.unit_nav,
                    accum_nav=nav_data.accum_nav
                )
                self.db.add(new_nav)
                self.db.commit()
                logger.info(f"创建净值记录: {nav_data.fund_code} - {nav_date}")
                return new_nav, True
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建/更新净值记录失败: {str(e)}")
            raise
    
    def get_nav_list(self, 
                     fund_code: Optional[str] = None,
                     start_date: Optional[date] = None,
                     end_date: Optional[date] = None,
                     page: int = 1,
                     page_size: int = 50,
                     sort_by: Optional[str] = "nav_date",
                     sort_order: Optional[str] = "desc") -> Tuple[List[Nav], int]:
        """
        获取净值列表（带分页和筛选）
        返回: (净值记录列表, 总记录数)
        """
        try:
            # 构建查询
            query = self.db.query(Nav).join(Fund)
            
            # 应用筛选条件
            if fund_code:
                query = query.filter(Nav.fund_code == fund_code)
            if start_date:
                query = query.filter(Nav.nav_date >= start_date)
            if end_date:
                query = query.filter(Nav.nav_date <= end_date)
            
            # 获取总数
            total = query.count()
            
            # 应用排序
            sort_column = getattr(Nav, sort_by) if hasattr(Nav, sort_by) else Nav.nav_date
            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
                
            # 应用分页
            nav_records = query.offset((page - 1) * page_size)\
                              .limit(page_size)\
                              .all()
            
            return nav_records, total
            
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
                nav_record = self.db.query(Nav).filter(Nav.id == nav_id).first()
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
    
    def process_excel_upload(self, file_content: bytes, filename: str) -> NavUploadResponse:
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
                # 中文字段名映射到英文字段名
                '基金代码': 'fund_code',
                '产品名称': 'fund_name',
                '净值日期': 'nav_date', 
                '单位净值': 'unit_nav',
                '累计净值': 'accum_nav',
                # 支持英文字段名（原有兼容性）
                'fund_code': 'fund_code',
                'fund_name': 'fund_name',
                'nav_date': 'nav_date',
                'unit_nav': 'unit_nav',
                'accum_nav': 'accum_nav'
            }
            
            # 转换列名为标准英文字段
            df_columns_mapped = {}
            for col in df.columns:
                col_str = str(col).strip()
                if col_str in column_mapping:
                    df_columns_mapped[col] = column_mapping[col_str]
                else:
                    df_columns_mapped[col] = col_str
            
            # 重命名列
            df = df.rename(columns=df_columns_mapped)
            
            logger.info(f"Excel文件列名: {list(df.columns)}")
            
            # 验证必要列是否存在
            required_columns = ['fund_code', 'nav_date', 'unit_nav', 'accum_nav']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                # 提供更友好的错误信息
                missing_chinese = []
                for missing_col in missing_columns:
                    for cn_name, en_name in column_mapping.items():
                        if en_name == missing_col:
                            missing_chinese.append(f"{cn_name}({missing_col})")
                            break
                    else:
                        missing_chinese.append(missing_col)
                
                error_msg = f"Excel文件缺少必要列: {', '.join(missing_chinese)}"
                errors.append(error_msg)
                return NavUploadResponse(
                    success_count=0,
                    failed_count=len(df) if len(df) > 0 else 1,
                    updated_count=0,
                    created_count=0,
                    errors=errors
                )
            
            # 逐行处理数据
            for index, row in df.iterrows():
                try:
                    # 验证和清理数据
                    fund_code = str(row['fund_code']).strip().upper() if pd.notna(row['fund_code']) else None
                    fund_name = str(row['fund_name']).strip() if 'fund_name' in row and pd.notna(row['fund_name']) else None
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
                    
                    # 创建NavManualCreate对象
                    nav_data = NavManualCreate(
                        fund_code=fund_code,
                        fund_name=fund_name,
                        nav_date=nav_date_str,
                        unit_nav=Decimal(str(unit_nav)),
                        accum_nav=Decimal(str(accum_nav))
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
            
            return NavUploadResponse(
                success_count=success_count,
                failed_count=failed_count,
                updated_count=updated_count,
                created_count=created_count,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Excel文件处理异常: {str(e)}"
            logger.error(error_msg)
            return NavUploadResponse(
                success_count=0,
                failed_count=0,
                updated_count=0,
                created_count=0,
                errors=[error_msg]
            )
    
    def get_nav_by_fund(self, fund_code: str, limit: int = 10) -> List[Nav]:
        """获取指定基金的最新净值记录"""
        try:
            nav_records = self.db.query(Nav).filter(Nav.fund_code == fund_code)\
                                           .order_by(desc(Nav.nav_date))\
                                           .limit(limit)\
                                           .all()
            return nav_records
        except Exception as e:
            logger.error(f"获取基金净值失败: {str(e)}")
            raise
    
    def calculate_nav_statistics(self, fund_code: str, days: int = 30) -> Dict:
        """计算净值统计信息"""
        try:
            nav_records = self.db.query(Nav).filter(Nav.fund_code == fund_code)\
                                           .order_by(desc(Nav.nav_date))\
                                           .limit(days)\
                                           .all()
            
            if not nav_records:
                return {"error": "没有找到净值数据"}
            
            # 转换为pandas DataFrame进行统计
            df = pd.DataFrame([{
                'nav_date': record.nav_date,
                'unit_nav': float(record.unit_nav),
                'accum_nav': float(record.accum_nav)
            } for record in nav_records])
            
            df = df.sort_values('nav_date')
            
            # 计算统计指标
            latest_nav = float(nav_records[0].unit_nav)
            earliest_nav = float(nav_records[-1].unit_nav) if len(nav_records) > 1 else latest_nav
            
            statistics = {
                "fund_code": fund_code,
                "latest_nav": latest_nav,
                "latest_date": nav_records[0].nav_date.isoformat(),
                "period_return": round((latest_nav / earliest_nav - 1) * 100, 2) if earliest_nav > 0 else 0,
                "max_nav": float(df['unit_nav'].max()),
                "min_nav": float(df['unit_nav'].min()),
                "avg_nav": round(float(df['unit_nav'].mean()), 4),
                "volatility": round(float(df['unit_nav'].std()), 4),
                "records_count": len(nav_records)
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"计算净值统计失败: {str(e)}")
            raise