"""
Tushare Pro API 路由
用于管理基准指数数据
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.services.tushare_service import TushareIndexService, SUPPORTED_INDICES, DEFAULT_START_DATE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tushare", tags=["tushare"])


@router.get("/indices/supported")
async def get_supported_indices():
    """
    获取支持的指数列表
    """
    indices = []
    for ts_code, name in SUPPORTED_INDICES.items():
        indices.append({
            'ts_code': ts_code,
            'index_name': name
        })
    return {
        'status': 'success',
        'data': indices
    }


@router.get("/indices/status")
async def get_indices_status(db: Session = Depends(get_db)):
    """
    获取所有指数的状态信息
    """
    try:
        service = TushareIndexService(db)
        status_list = service.get_all_indices_status()
        return {
            'status': 'success',
            'data': status_list
        }
    except Exception as e:
        logger.error(f"获取指数状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indices/{ts_code}/initialize")
async def initialize_index(
    ts_code: str,
    start_date: str = Query(default=DEFAULT_START_DATE, description="初始化起始日期，格式 YYYYMMDD"),
    db: Session = Depends(get_db)
):
    """
    初始化指数数据（首次使用）

    - 从指定起始日期开始获取完整历史数据
    - 仅在本地不存在数据时执行
    - 数据来源：Tushare Pro index_daily 接口
    """
    if ts_code not in SUPPORTED_INDICES:
        raise HTTPException(status_code=400, detail=f"不支持的指数代码: {ts_code}")

    try:
        service = TushareIndexService(db)
        index_name = SUPPORTED_INDICES[ts_code]
        result = service.initialize_index(ts_code, index_name, start_date)
        return result
    except Exception as e:
        logger.error(f"初始化指数失败: {ts_code}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indices/{ts_code}/update")
async def update_index(ts_code: str, db: Session = Depends(get_db)):
    """
    增量更新指数数据

    - 自动从本地最新交易日 + 1 开始获取
    - 仅追加新数据，不覆盖历史
    - 如果已是最新，返回提示信息
    """
    if ts_code not in SUPPORTED_INDICES:
        raise HTTPException(status_code=400, detail=f"不支持的指数代码: {ts_code}")

    try:
        service = TushareIndexService(db)
        result = service.update_index_incremental(ts_code)
        return result
    except Exception as e:
        logger.error(f"更新指数失败: {ts_code}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indices/update-all")
async def update_all_indices(db: Session = Depends(get_db)):
    """
    批量增量更新所有已初始化的指数
    """
    try:
        service = TushareIndexService(db)
        results = []

        for ts_code in SUPPORTED_INDICES.keys():
            try:
                result = service.update_index_incremental(ts_code)
                results.append({
                    'ts_code': ts_code,
                    **result
                })
            except Exception as e:
                results.append({
                    'ts_code': ts_code,
                    'status': 'error',
                    'message': str(e)
                })

        return {
            'status': 'success',
            'data': results
        }
    except Exception as e:
        logger.error(f"批量更新指数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices/{ts_code}/data")
async def get_index_data(
    ts_code: str,
    start_date: Optional[str] = Query(None, description="开始日期，格式 YYYYMMDD 或 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式 YYYYMMDD 或 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取指数历史数据

    - 返回格式: [{'date': 'YYYY-MM-DD', 'value': close_price}, ...]
    - 用于前端计算超额收益
    - 按交易日升序排列
    """
    if ts_code not in SUPPORTED_INDICES:
        raise HTTPException(status_code=400, detail=f"不支持的指数代码: {ts_code}")

    try:
        service = TushareIndexService(db)
        data = service.get_index_data(ts_code, start_date, end_date)

        if not data:
            return {
                'status': 'no_data',
                'message': f'指数 {ts_code} 暂无数据，请先调用初始化接口',
                'data': []
            }

        return {
            'status': 'success',
            'ts_code': ts_code,
            'index_name': SUPPORTED_INDICES[ts_code],
            'count': len(data),
            'data': data
        }
    except Exception as e:
        logger.error(f"获取指数数据失败: {ts_code}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indices/initialize-all")
async def initialize_all_indices(
    start_date: str = Query(default=DEFAULT_START_DATE, description="初始化起始日期，格式 YYYYMMDD"),
    db: Session = Depends(get_db)
):
    """
    批量初始化所有支持的指数

    注意：此操作会从 Tushare 拉取大量数据，请谨慎使用
    """
    try:
        service = TushareIndexService(db)
        results = []

        for ts_code, index_name in SUPPORTED_INDICES.items():
            try:
                result = service.initialize_index(ts_code, index_name, start_date)
                results.append({
                    'ts_code': ts_code,
                    **result
                })
            except Exception as e:
                results.append({
                    'ts_code': ts_code,
                    'status': 'error',
                    'message': str(e)
                })

        return {
            'status': 'success',
            'data': results
        }
    except Exception as e:
        logger.error(f"批量初始化指数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
