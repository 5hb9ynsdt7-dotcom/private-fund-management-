"""
Tushare Pro 数据服务
用于获取和管理指数基准数据
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from ..models import IndexDaily, IndexMeta
from ..database import get_db

logger = logging.getLogger(__name__)

# Tushare Pro Token
TUSHARE_TOKEN = "741685d4e34ced0e4e7e0439d7e013a24e1dd31aff685f06cf51a683"

# 初始化 Tushare Pro
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

# 支持的指数定义
SUPPORTED_INDICES = {
    '000300.SH': '沪深300',
    '000905.SH': '中证500',
    '000852.SH': '中证1000',
    '000510.SH': '中证A500',
    '000906.SH': '中证800',
    '932000.CSI': '中证2000',
    '000001.SH': '上证指数',
}

# 默认初始化起始日期（可根据需求调整）
DEFAULT_START_DATE = '20200101'


class TushareIndexService:
    """Tushare 指数数据服务"""

    def __init__(self, db: Session):
        self.db = db
        self.pro = pro

    def get_or_create_meta(self, ts_code: str, index_name: str,
                          initial_start_date: str = DEFAULT_START_DATE) -> IndexMeta:
        """
        获取或创建指数元数据
        """
        meta = self.db.query(IndexMeta).filter(IndexMeta.ts_code == ts_code).first()

        if not meta:
            meta = IndexMeta(
                ts_code=ts_code,
                index_name=index_name,
                initial_start_date=initial_start_date,
                latest_trade_date=None,
                total_records=0,
                is_active=True
            )
            self.db.add(meta)
            self.db.commit()
            self.db.refresh(meta)
            logger.info(f"创建指数元数据: {ts_code} - {index_name}")

        return meta

    def fetch_from_tushare(self, ts_code: str, start_date: str,
                          end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        从 Tushare Pro 获取指数日行情数据

        Args:
            ts_code: 指数代码，如 '000300.SH'
            start_date: 开始日期，格式 'YYYYMMDD'
            end_date: 结束日期，格式 'YYYYMMDD'，默认为当前日期

        Returns:
            DataFrame 或 None
        """
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')

            logger.info(f"从 Tushare 获取指数数据: {ts_code}, {start_date} -> {end_date}")

            # 调用 Tushare Pro index_daily 接口
            df = self.pro.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,close,open,high,low,pre_close,change,pct_chg,vol,amount'
            )

            if df is None or df.empty:
                logger.warning(f"Tushare 返回空数据: {ts_code}, {start_date} -> {end_date}")
                return None

            logger.info(f"成功获取 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"Tushare API 调用失败: {ts_code}, {e}")
            return None

    def save_index_data(self, df: pd.DataFrame, ts_code: str) -> int:
        """
        保存指数数据到数据库（批量插入，跳过重复）

        Returns:
            成功插入的记录数
        """
        if df is None or df.empty:
            return 0

        inserted_count = 0

        for _, row in df.iterrows():
            try:
                # 检查是否已存在
                exists = self.db.query(IndexDaily).filter(
                    and_(
                        IndexDaily.ts_code == ts_code,
                        IndexDaily.trade_date == row['trade_date']
                    )
                ).first()

                if exists:
                    continue  # 跳过已存在的记录

                # 插入新记录
                index_daily = IndexDaily(
                    ts_code=row['ts_code'],
                    trade_date=row['trade_date'],
                    close=float(row['close']) if pd.notna(row['close']) else None,
                    open=float(row['open']) if pd.notna(row['open']) else None,
                    high=float(row['high']) if pd.notna(row['high']) else None,
                    low=float(row['low']) if pd.notna(row['low']) else None,
                    pre_close=float(row['pre_close']) if pd.notna(row['pre_close']) else None,
                    change=float(row['change']) if pd.notna(row['change']) else None,
                    pct_chg=float(row['pct_chg']) if pd.notna(row['pct_chg']) else None,
                    vol=float(row['vol']) if pd.notna(row['vol']) else None,
                    amount=float(row['amount']) if pd.notna(row['amount']) else None,
                )
                self.db.add(index_daily)
                inserted_count += 1

            except Exception as e:
                logger.error(f"保存数据失败: {row['trade_date']}, {e}")
                continue

        if inserted_count > 0:
            self.db.commit()
            logger.info(f"成功插入 {inserted_count} 条新记录")

        return inserted_count

    def update_meta_latest_date(self, ts_code: str):
        """
        更新元数据中的最新交易日期和总记录数
        """
        meta = self.db.query(IndexMeta).filter(IndexMeta.ts_code == ts_code).first()

        if not meta:
            return

        # 查询最新交易日期
        latest_record = self.db.query(IndexDaily).filter(
            IndexDaily.ts_code == ts_code
        ).order_by(desc(IndexDaily.trade_date)).first()

        if latest_record:
            meta.latest_trade_date = latest_record.trade_date

        # 更新总记录数
        total = self.db.query(IndexDaily).filter(IndexDaily.ts_code == ts_code).count()
        meta.total_records = total

        self.db.commit()
        logger.info(f"更新元数据: {ts_code}, latest={meta.latest_trade_date}, total={total}")

    def initialize_index(self, ts_code: str, index_name: str,
                        start_date: str = DEFAULT_START_DATE) -> Dict:
        """
        首次初始化指数数据（完整历史区间）

        Returns:
            包含初始化结果的字典
        """
        logger.info(f"开始初始化指数: {ts_code} - {index_name}, 起始日期: {start_date}")

        # 检查是否已初始化
        meta = self.db.query(IndexMeta).filter(IndexMeta.ts_code == ts_code).first()
        if meta and meta.total_records > 0:
            return {
                'status': 'already_initialized',
                'message': f'指数 {ts_code} 已存在 {meta.total_records} 条记录',
                'latest_date': meta.latest_trade_date
            }

        # 创建元数据
        meta = self.get_or_create_meta(ts_code, index_name, start_date)

        # 从 Tushare 获取完整历史数据
        df = self.fetch_from_tushare(ts_code, start_date)

        if df is None or df.empty:
            return {
                'status': 'error',
                'message': f'获取指数 {ts_code} 数据失败或无数据'
            }

        # 保存数据
        inserted_count = self.save_index_data(df, ts_code)

        # 更新元数据
        self.update_meta_latest_date(ts_code)

        return {
            'status': 'success',
            'message': f'成功初始化指数 {ts_code}',
            'inserted_count': inserted_count,
            'latest_date': meta.latest_trade_date
        }

    def update_index_incremental(self, ts_code: str) -> Dict:
        """
        增量更新指数数据（仅获取最新交易日之后的数据）

        核心逻辑：
        1. 读取本地最新交易日
        2. 从 latest_date + 1 开始请求
        3. 仅追加新增数据

        Returns:
            包含更新结果的字典
        """
        logger.info(f"开始增量更新指数: {ts_code}")

        # 获取元数据
        meta = self.db.query(IndexMeta).filter(IndexMeta.ts_code == ts_code).first()

        if not meta or not meta.latest_trade_date:
            return {
                'status': 'not_initialized',
                'message': f'指数 {ts_code} 未初始化，请先调用初始化接口'
            }

        # 计算起始日期（最新日期 + 1 天）
        latest_date = datetime.strptime(meta.latest_trade_date, '%Y%m%d')
        start_date = (latest_date + timedelta(days=1)).strftime('%Y%m%d')
        end_date = datetime.now().strftime('%Y%m%d')

        # 如果起始日期大于等于今天，说明已是最新
        if start_date >= end_date:
            return {
                'status': 'up_to_date',
                'message': f'数据已是最新，最新交易日: {meta.latest_trade_date}'
            }

        # 从 Tushare 获取增量数据
        df = self.fetch_from_tushare(ts_code, start_date, end_date)

        if df is None or df.empty:
            return {
                'status': 'no_new_data',
                'message': f'无新交易数据（可能为非交易日），最新日期: {meta.latest_trade_date}'
            }

        # 保存新数据
        inserted_count = self.save_index_data(df, ts_code)

        # 更新元数据
        self.update_meta_latest_date(ts_code)

        return {
            'status': 'success',
            'message': f'成功更新指数 {ts_code}',
            'inserted_count': inserted_count,
            'previous_latest': meta.latest_trade_date,
            'new_latest': self.db.query(IndexMeta).filter(
                IndexMeta.ts_code == ts_code
            ).first().latest_trade_date
        }

    def get_index_data(self, ts_code: str, start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> List[Dict]:
        """
        获取本地存储的指数数据

        Args:
            ts_code: 指数代码
            start_date: 开始日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYYMMDD' 或 'YYYY-MM-DD'

        Returns:
            指数数据列表，格式: [{'date': 'YYYY-MM-DD', 'value': close_price}, ...]
        """
        query = self.db.query(IndexDaily).filter(IndexDaily.ts_code == ts_code)

        # 日期格式转换（支持 YYYYMMDD 和 YYYY-MM-DD）
        if start_date:
            start_date = start_date.replace('-', '')
            query = query.filter(IndexDaily.trade_date >= start_date)

        if end_date:
            end_date = end_date.replace('-', '')
            query = query.filter(IndexDaily.trade_date <= end_date)

        records = query.order_by(IndexDaily.trade_date).all()

        # 转换为前端需要的格式
        result = []
        for record in records:
            # 将 YYYYMMDD 转换为 YYYY-MM-DD
            date_str = f"{record.trade_date[:4]}-{record.trade_date[4:6]}-{record.trade_date[6:]}"
            result.append({
                'date': date_str,
                'value': float(record.close) if record.close else None
            })

        return result

    def get_all_indices_status(self) -> List[Dict]:
        """
        获取所有指数的状态信息
        """
        metas = self.db.query(IndexMeta).all()

        result = []
        for meta in metas:
            result.append({
                'ts_code': meta.ts_code,
                'index_name': meta.index_name,
                'latest_trade_date': meta.latest_trade_date,
                'total_records': meta.total_records,
                'last_update_time': meta.last_update_time.isoformat() if meta.last_update_time else None,
                'is_active': meta.is_active
            })

        return result


def get_tushare_service(db: Session = None) -> TushareIndexService:
    """
    获取 Tushare 服务实例（依赖注入）
    """
    if db is None:
        db = next(get_db())
    return TushareIndexService(db)
