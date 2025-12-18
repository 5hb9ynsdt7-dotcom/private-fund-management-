"""
量化分析API路由
"""
from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.models import Strategy, Nav, Fund
from app.services.quantitative_service import QuantitativeService
import subprocess
import urllib.parse

router = APIRouter(prefix="/api/quantitative", tags=["quantitative"])

# 初始化量化服务（不传入db，在使用时动态设置）
quant_service_template = QuantitativeService()

# 指数secid映射（用于代理请求）
INDEX_SECID_MAP = {
    '000905.SH': '0.399905',  # 中证500
    '399300.SZ': '0.399300',  # 沪深300
    '000906.SH': '1.000906',  # 中证800
    '000510.SH': '1.000510',  # 中证A500
    '399852.SZ': '0.399852',  # 中证1000
    '932000.CS': '1.932000',  # 中证2000
    '000001.SH': '1.000001',  # 上证指数
}


@router.get("/fetch-index-proxy/{index_code}")
async def fetch_index_proxy(index_code: str):
    """
    代理获取指数数据（绕过前端CORS限制）
    使用curl从东方财富API获取数据并返回给前端
    """
    try:
        secid = INDEX_SECID_MAP.get(index_code)
        if not secid:
            raise HTTPException(status_code=400, detail=f"未知的指数代码: {index_code}")

        # 构建API URL
        url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&end=20500101&lmt=3000"

        # 使用curl获取数据
        curl_cmd = ['curl', '-s', '--max-time', '10', '--compressed', url]
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=15)

        if result.returncode != 0:
            print(f"curl获取指数 {index_code} 失败: {result.stderr}")
            raise HTTPException(status_code=502, detail="获取指数数据失败")

        response_text = result.stdout
        if not response_text:
            raise HTTPException(status_code=502, detail="API返回空响应")

        # 解析JSON（处理可能的JSONP格式）
        if '(' in response_text and ')' in response_text:
            json_str = response_text[response_text.find('(') + 1:response_text.rfind(')')]
            data = json.loads(json_str)
        else:
            data = json.loads(response_text)

        if not data.get('data') or not data['data'].get('klines'):
            raise HTTPException(status_code=502, detail="API返回数据格式错误")

        # 解析K线数据
        klines = data['data']['klines']
        benchmark_data = []
        for kline in klines:
            parts = kline.split(',')
            if len(parts) >= 2:
                benchmark_data.append({
                    'date': parts[0],
                    'value': float(parts[1])
                })

        print(f"成功代理获取指数 {index_code} 数据，共 {len(benchmark_data)} 条")
        return benchmark_data

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="请求超时")
    except HTTPException:
        raise
    except Exception as e:
        print(f"代理获取指数数据异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products")
async def get_quantitative_products(
    product_type: Optional[str] = Query(None),
    tracking_index: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取量化多头产品列表（仅返回有净值的产品）"""
    try:
        # 从数据库获取所有量化多头策略，联合查询Fund表获取产品名称
        query = db.query(Strategy, Fund).join(
            Fund, Strategy.fund_code == Fund.fund_code
        ).filter(Strategy.sub_strategy == "量化多头")

        strategies = query.all()

        # 转换为前端需要的格式
        products = []
        for strategy, fund in strategies:
            # 获取最新净值
            latest_nav = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date.desc()).first()

            # 只返回有净值的产品
            if not latest_nav:
                continue

            # 智能识别跟踪指数和产品类型
            fund_name = fund.fund_name
            tracking_index = ""
            product_type_detected = ""

            # 注意:先检查更具体的指数(如A500),再检查通用的(如500)
            if "中证A500" in fund_name or "A500" in fund_name:
                tracking_index = "000510.SH"
                product_type_detected = "A500指增"
            elif "中证500" in fund_name or "500" in fund_name:
                tracking_index = "000905.SH"
                product_type_detected = "500指增"
            elif "沪深300" in fund_name or "300" in fund_name:
                tracking_index = "000300.SH"
                product_type_detected = "300指增"
            elif "中证1000" in fund_name or "1000" in fund_name:
                tracking_index = "000852.SH"
                product_type_detected = "1000指增"
            elif "中证800" in fund_name or "800" in fund_name:
                tracking_index = "000906.SH"
                product_type_detected = "800指增"
            elif "中证2000" in fund_name or "2000" in fund_name:
                tracking_index = "932000.CSI"
                product_type_detected = "2000指增"
            else:
                product_type_detected = "量化选股"

            product = {
                "productName": fund.fund_name,
                "displayName": fund.fund_name.replace("龙舟-", "").replace("私募证券投资基金", "").rstrip("-"),
                "fundCode": fund.fund_code,
                "productType": product_type_detected,
                "trackingIndex": tracking_index,
                "strategy": strategy.sub_strategy,
                "mainStrategy": strategy.main_strategy,
                "manager": "",  # 基金管理人字段暂时为空
                "latestNav": float(latest_nav.unit_nav),
                "latestDate": latest_nav.nav_date.strftime("%Y-%m-%d")
            }
            products.append(product)

        # 按产品名称排序
        products.sort(key=lambda x: x['displayName'])

        return products

    except Exception as e:
        print(f"获取产品列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/{fund_code}")
async def get_product_info(fund_code: str, db: Session = Depends(get_db)):
    """获取单个产品详细信息"""
    try:
        # 查询策略和基金信息
        result = db.query(Strategy, Fund).join(
            Fund, Strategy.fund_code == Fund.fund_code
        ).filter(Strategy.fund_code == fund_code).first()

        if not result:
            raise HTTPException(status_code=404, detail="产品未找到")

        strategy, fund = result

        # 获取最新净值
        latest_nav = db.query(Nav).filter(
            Nav.fund_code == fund_code
        ).order_by(Nav.nav_date.desc()).first()

        # 智能识别跟踪指数
        fund_name = fund.fund_name
        tracking_index = ""
        product_type = ""

        # 注意:先检查更具体的指数(如A500),再检查通用的(如500)
        if "中证A500" in fund_name or "A500" in fund_name:
            tracking_index = "000510.SH"
            product_type = "A500指增"
        elif "中证500" in fund_name or "500" in fund_name:
            tracking_index = "000905.SH"
            product_type = "500指增"
        elif "沪深300" in fund_name or "300" in fund_name:
            tracking_index = "000300.SH"
            product_type = "300指增"
        elif "中证1000" in fund_name or "1000" in fund_name:
            tracking_index = "000852.SH"
            product_type = "1000指增"
        else:
            product_type = "量化选股"

        return {
            "productName": fund.fund_name,
            "displayName": fund.fund_name.replace("龙舟-", "").replace("私募证券投资基金", ""),
            "productCode": fund.fund_code,
            "productType": product_type,
            "trackingIndex": tracking_index,
            "strategy": strategy.sub_strategy,
            "mainStrategy": strategy.main_strategy,
            "manager": "",  # 基金管理人字段暂时为空
            "latestNav": float(latest_nav.unit_nav) if latest_nav else None,
            "latestDate": latest_nav.nav_date.strftime("%Y-%m-%d") if latest_nav else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product-nav/{fund_code}")
async def get_product_nav(
    fund_code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取产品净值数据"""
    try:
        query = db.query(Nav).filter(Nav.fund_code == fund_code)

        if start_date:
            query = query.filter(Nav.nav_date >= datetime.strptime(start_date, "%Y-%m-%d"))

        if end_date:
            query = query.filter(Nav.nav_date <= datetime.strptime(end_date, "%Y-%m-%d"))

        nav_data = query.order_by(Nav.nav_date).all()

        return [
            {
                "date": nav.nav_date.strftime("%Y-%m-%d"),
                "value": float(nav.unit_nav),
                "accumValue": float(nav.accum_nav)
            }
            for nav in nav_data
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index-data")
async def get_index_data(
    index_code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """获取指数数据（从东方财富API）"""
    try:
        # 构建东方财富API请求
        # 这里使用示例数据，实际需要对接东方财富API
        index_data = await quant_service_template.fetch_index_data(
            index_code, start_date, end_date
        )

        return index_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/product-config")
async def save_product_config(
    config: Dict[str, str],
    db: Session = Depends(get_db)
):
    """保存产品配置（跟踪指数和产品类型）"""
    try:
        fund_code = config.get("fundCode")
        tracking_index = config.get("trackingIndex")
        product_type = config.get("productType")

        # 这里暂时将配置存储在内存中或缓存中
        # 实际应该添加新的字段到Strategy表或创建新的配置表

        return {"message": "配置保存成功"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/product-configs")
async def save_batch_configs(
    data: Dict[str, List],
    db: Session = Depends(get_db)
):
    """批量保存产品配置"""
    try:
        products = data.get("products", [])

        # 批量保存配置
        for product in products:
            # 这里暂时将配置存储在内存中或缓存中
            # 实际应该添加新的字段到Strategy表或创建新的配置表
            pass

        return {"message": f"成功更新 {len(products)} 个产品配置"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-monthly-excess")
async def calculate_monthly_excess(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    计算月度超额收益
    支持两种模式：
    1. 后端获取指数数据（默认）
    2. 前端传入指数数据：request_data.indexDataMap = {index_code: [{date, value}, ...]}
    3. 前端传入产品配置：request_data.productConfigs = {fund_code: {trackingIndex, productType}}
    """
    try:
        year = request_data.get("year", datetime.now().year)
        # 前端传入的指数数据映射
        index_data_map = request_data.get("indexDataMap", {})
        # 前端传入的产品配置
        product_configs = request_data.get("productConfigs", {})

        # 获取所有量化多头产品
        products_query = db.query(Strategy, Fund).join(
            Fund, Strategy.fund_code == Fund.fund_code
        ).filter(Strategy.sub_strategy == "量化多头")

        strategies = products_query.all()

        results = []

        for strategy, fund in strategies:
            # 获取最新净值，过滤无净值产品
            latest_nav = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date.desc()).first()

            if not latest_nav:
                continue

            # 优先使用前端传入的配置，否则通过产品名称智能识别
            fund_code = fund.fund_code
            if fund_code in product_configs:
                # 使用前端保存的配置
                tracking_index = product_configs[fund_code].get("trackingIndex", "")
                product_type_detected = product_configs[fund_code].get("productType", "")
                print(f"使用配置: {fund_code} -> {tracking_index}, {product_type_detected}")
            else:
                # 智能识别跟踪指数和产品类型
                tracking_index = ""
                product_type_detected = ""
                fund_name = fund.fund_name

                # 注意:先检查更具体的指数(如A500),再检查通用的(如500)
                if "中证A500" in fund_name or "A500" in fund_name:
                    tracking_index = "000510.SH"
                    product_type_detected = "A500指增"
                elif "中证500" in fund_name or "500" in fund_name:
                    tracking_index = "000905.SH"
                    product_type_detected = "500指增"
                elif "沪深300" in fund_name or "300" in fund_name:
                    tracking_index = "000300.SH"
                    product_type_detected = "300指增"
                elif "中证1000" in fund_name or "1000" in fund_name:
                    tracking_index = "000852.SH"
                    product_type_detected = "1000指增"
                elif "中证800" in fund_name or "800" in fund_name:
                    tracking_index = "000906.SH"
                    product_type_detected = "800指增"
                elif "中证2000" in fund_name or "2000" in fund_name:
                    tracking_index = "932000.CSI"
                    product_type_detected = "2000指增"
                else:
                    product_type_detected = "量化选股"

                print(f"智能识别: {fund_code} -> {tracking_index}, {product_type_detected}")

            if not tracking_index:
                print(f"跳过 {fund_code}：无跟踪指数")
                continue

            # 获取产品净值数据
            nav_data = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date).all()

            # 获取指数数据（优先使用前端传入的数据，否则从Tushare数据库获取）
            if tracking_index in index_data_map and index_data_map[tracking_index]:
                index_data = index_data_map[tracking_index]
                print(f"使用前端传入的 {tracking_index} 指数数据，共 {len(index_data)} 条")
            else:
                # 从Tushare数据库获取指数数据
                from app.services.tushare_service import TushareIndexService
                tushare_service = TushareIndexService(db)
                index_data = tushare_service.get_index_data(
                    tracking_index,
                    f"{year-1}-01-01",
                    f"{year}-12-31"
                )
                print(f"从Tushare数据库获取 {tracking_index} 指数数据，共 {len(index_data)} 条")

            # 验证指数数据是否为空
            if not index_data or len(index_data) == 0:
                print(f"⚠️ 跳过 {fund_code}：指数 {tracking_index} 数据为空，请检查Tushare数据库中是否有该指数数据")
                continue

            # 创建带db的quant_service实例
            quant_service = QuantitativeService(db)

            # 计算月度超额（传入fund_code以支持分红调整）
            monthly_excess = quant_service.calculate_monthly_excess(
                nav_data, index_data, year, fund_code
            )

            results.append({
                "productName": fund.fund_name,
                "displayName": fund.fund_name.replace("龙舟-", "").replace("私募证券投资基金", "").rstrip("-"),
                "fundCode": fund.fund_code,
                "productType": product_type_detected,
                "trackingIndex": tracking_index,  # 添加基准指数代码
                **monthly_excess
            })

        return results

    except Exception as e:
        print(f"计算月度超额失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-yearly-excess")
async def calculate_yearly_excess(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    计算年度超额收益
    支持前端传入指数数据：request_data.indexDataMap
    支持前端传入产品配置：request_data.productConfigs
    """
    try:
        start_year = request_data.get("startYear", 2020)
        end_year = request_data.get("endYear", datetime.now().year)
        years = list(range(start_year, end_year + 1))
        index_data_map = request_data.get("indexDataMap", {})
        product_configs = request_data.get("productConfigs", {})

        # 获取所有量化多头产品
        products_query = db.query(Strategy, Fund).join(
            Fund, Strategy.fund_code == Fund.fund_code
        ).filter(Strategy.sub_strategy == "量化多头")

        strategies = products_query.all()

        results = []

        for strategy, fund in strategies:
            # 获取最新净值，过滤无净值产品
            latest_nav = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date.desc()).first()

            if not latest_nav:
                continue

            # 优先使用前端传入的配置，否则通过产品名称智能识别
            fund_code = fund.fund_code
            if fund_code in product_configs:
                # 使用前端保存的配置
                tracking_index = product_configs[fund_code].get("trackingIndex", "")
                product_type_detected = product_configs[fund_code].get("productType", "")
            else:
                # 智能识别跟踪指数和产品类型
                tracking_index = ""
                product_type_detected = ""
                fund_name = fund.fund_name

                # 注意:先检查更具体的指数(如A500),再检查通用的(如500)
                if "中证A500" in fund_name or "A500" in fund_name:
                    tracking_index = "000510.SH"
                    product_type_detected = "A500指增"
                elif "中证500" in fund_name or "500" in fund_name:
                    tracking_index = "000905.SH"
                    product_type_detected = "500指增"
                elif "沪深300" in fund_name or "300" in fund_name:
                    tracking_index = "000300.SH"
                    product_type_detected = "300指增"
                elif "中证1000" in fund_name or "1000" in fund_name:
                    tracking_index = "000852.SH"
                    product_type_detected = "1000指增"
                elif "中证800" in fund_name or "800" in fund_name:
                    tracking_index = "000906.SH"
                    product_type_detected = "800指增"
                elif "中证2000" in fund_name or "2000" in fund_name:
                    tracking_index = "932000.CSI"
                    product_type_detected = "2000指增"
                else:
                    product_type_detected = "量化选股"

            if not tracking_index:
                continue

            # 获取产品净值数据
            nav_data = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date).all()

            # 获取指数数据（优先使用前端传入的数据，否则从Tushare数据库获取）
            if tracking_index in index_data_map and index_data_map[tracking_index]:
                index_data = index_data_map[tracking_index]
                print(f"使用前端传入的 {tracking_index} 指数数据，共 {len(index_data)} 条")
            else:
                # 从Tushare数据库获取指数数据
                from app.services.tushare_service import TushareIndexService
                tushare_service = TushareIndexService(db)
                index_data = tushare_service.get_index_data(
                    tracking_index,
                    f"{start_year-1}-01-01",
                    f"{end_year}-12-31"
                )
                print(f"从Tushare数据库获取 {tracking_index} 指数数据，共 {len(index_data)} 条")

            # 验证指数数据是否为空
            if not index_data or len(index_data) == 0:
                print(f"⚠️ 跳过 {fund_code}：指数 {tracking_index} 数据为空，请检查Tushare数据库中是否有该指数数据")
                continue

            # 创建带db的quant_service实例
            quant_service = QuantitativeService(db)

            # 计算年度超额（传入fund_code以支持分红调整）
            yearly_excess = quant_service.calculate_yearly_excess(
                nav_data, index_data, years, fund_code
            )

            results.append({
                "productName": fund.fund_name,
                "displayName": fund.fund_name.replace("龙舟-", "").replace("私募证券投资基金", "").rstrip("-"),
                "fundCode": fund.fund_code,
                "productType": product_type_detected,
                "trackingIndex": tracking_index,  # 添加基准指数代码
                **yearly_excess
            })

        return results

    except Exception as e:
        print(f"计算年度超额失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-period-excess")
async def calculate_period_excess(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    计算区间超额收益
    支持前端传入指数数据：request_data.indexDataMap
    支持前端传入产品配置：request_data.productConfigs
    """
    try:
        start_date = request_data.get("startDate")
        end_date = request_data.get("endDate")
        index_data_map = request_data.get("indexDataMap", {})
        product_configs = request_data.get("productConfigs", {})

        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="请提供起止日期")

        # 获取所有量化多头产品
        products_query = db.query(Strategy, Fund).join(
            Fund, Strategy.fund_code == Fund.fund_code
        ).filter(Strategy.sub_strategy == "量化多头")

        strategies = products_query.all()

        results = []

        for strategy, fund in strategies:
            # 获取最新净值，过滤无净值产品
            latest_nav = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date.desc()).first()

            if not latest_nav:
                continue

            # 优先使用前端传入的配置，否则通过产品名称智能识别
            fund_code = fund.fund_code
            if fund_code in product_configs:
                # 使用前端保存的配置
                tracking_index = product_configs[fund_code].get("trackingIndex", "")
                product_type_detected = product_configs[fund_code].get("productType", "")
            else:
                # 智能识别跟踪指数和产品类型
                tracking_index = ""
                product_type_detected = ""
                fund_name = fund.fund_name

                # 注意:先检查更具体的指数(如A500),再检查通用的(如500)
                if "中证A500" in fund_name or "A500" in fund_name:
                    tracking_index = "000510.SH"
                    product_type_detected = "A500指增"
                elif "中证500" in fund_name or "500" in fund_name:
                    tracking_index = "000905.SH"
                    product_type_detected = "500指增"
                elif "沪深300" in fund_name or "300" in fund_name:
                    tracking_index = "000300.SH"
                    product_type_detected = "300指增"
                elif "中证1000" in fund_name or "1000" in fund_name:
                    tracking_index = "000852.SH"
                    product_type_detected = "1000指增"
                elif "中证800" in fund_name or "800" in fund_name:
                    tracking_index = "000906.SH"
                    product_type_detected = "800指增"
                elif "中证2000" in fund_name or "2000" in fund_name:
                    tracking_index = "932000.CSI"
                    product_type_detected = "2000指增"
                else:
                    product_type_detected = "量化选股"

            if not tracking_index:
                continue

            # 获取产品净值数据
            nav_data = db.query(Nav).filter(
                Nav.fund_code == fund.fund_code
            ).order_by(Nav.nav_date).all()

            # 获取指数数据（优先使用前端传入的数据，否则从Tushare数据库获取）
            if tracking_index in index_data_map and index_data_map[tracking_index]:
                index_data = index_data_map[tracking_index]
                print(f"使用前端传入的 {tracking_index} 指数数据，共 {len(index_data)} 条")
            else:
                # 从Tushare数据库获取指数数据
                from app.services.tushare_service import TushareIndexService
                tushare_service = TushareIndexService(db)
                index_data = tushare_service.get_index_data(
                    tracking_index,
                    start_date,
                    end_date
                )
                print(f"从Tushare数据库获取 {tracking_index} 指数数据，共 {len(index_data)} 条")

            # 验证指数数据是否为空
            if not index_data or len(index_data) == 0:
                print(f"⚠️ 跳过 {fund_code}：指数 {tracking_index} 数据为空，请检查Tushare数据库中是否有该指数数据")
                continue

            # 创建带db的quant_service实例
            quant_service = QuantitativeService(db)

            # 计算区间超额（传入fund_code以支持分红调整）
            period_excess = quant_service.calculate_period_excess(
                nav_data, index_data, start_date, end_date, fund_code
            )

            if not period_excess:
                continue

            results.append({
                "productName": fund.fund_name,
                "displayName": fund.fund_name.replace("龙舟-", "").replace("私募证券投资基金", "").rstrip("-"),
                "fundCode": fund.fund_code,
                "productType": product_type_detected,
                "trackingIndex": tracking_index,  # 添加基准指数代码
                **period_excess
            })

        return results

    except HTTPException:
        raise
    except Exception as e:
        print(f"计算区间超额失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-metrics/{fund_code}")
async def get_risk_metrics(
    fund_code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """计算风险指标"""
    try:
        # 获取产品净值数据
        query = db.query(Nav).filter(Nav.fund_code == fund_code)

        if start_date:
            query = query.filter(Nav.nav_date >= datetime.strptime(start_date, "%Y-%m-%d"))

        if end_date:
            query = query.filter(Nav.nav_date <= datetime.strptime(end_date, "%Y-%m-%d"))

        nav_data = query.order_by(Nav.nav_date).all()

        # 获取产品信息来确定跟踪指数
        fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()

        if not fund:
            raise HTTPException(status_code=404, detail="产品未找到")

        # 智能识别跟踪指数
        tracking_index = ""
        fund_name = fund.fund_name

        # 注意:先检查更具体的指数(如A500),再检查通用的(如500)
        if "中证A500" in fund_name or "A500" in fund_name:
            tracking_index = "000510.SH"
        elif "中证500" in fund_name or "500" in fund_name:
            tracking_index = "000905.SH"
        elif "沪深300" in fund_name or "300" in fund_name:
            tracking_index = "399300.SZ"
        elif "中证1000" in fund_name or "1000" in fund_name:
            tracking_index = "399852.SZ"

        if not tracking_index:
            raise HTTPException(status_code=400, detail="无法识别产品跟踪指数")

        # 获取指数数据
        index_data = await quant_service_template.fetch_index_data(
            tracking_index, start_date, end_date
        )

        # 计算风险指标
        metrics = quant_service_template.calculate_risk_metrics(nav_data, index_data)

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-nav-date")
async def get_latest_nav_date(db: Session = Depends(get_db)):
    """
    获取数据库中最新的净值日期
    用于前端显示"今年以来(最新净值YYYYMMDD)"
    """
    try:
        latest_nav = db.query(Nav).order_by(Nav.nav_date.desc()).first()

        if not latest_nav:
            return {"latestNavDate": None}

        # 返回格式化的日期 YYYY-MM-DD
        return {"latestNavDate": latest_nav.nav_date.strftime("%Y-%m-%d")}

    except Exception as e:
        print(f"获取最新净值日期失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weekly-excess-curve")
async def get_weekly_excess_curve(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    获取单个产品的周度累计超额曲线数据（用于绘图）
    使用与月度超额计算相同的周度逻辑，确保分红处理一致
    """
    try:
        fund_code = request_data.get("fundCode")
        start_date = request_data.get("startDate")
        end_date = request_data.get("endDate")
        index_code = request_data.get("indexCode")
        index_data_map = request_data.get("indexDataMap", {})

        if not fund_code:
            raise HTTPException(status_code=400, detail="请提供基金代码")

        if not index_code:
            raise HTTPException(status_code=400, detail="请提供指数代码")

        # 获取净值数据
        nav_query = db.query(Nav).filter(Nav.fund_code == fund_code)
        if start_date:
            nav_query = nav_query.filter(Nav.nav_date >= datetime.strptime(start_date, "%Y-%m-%d"))
        if end_date:
            nav_query = nav_query.filter(Nav.nav_date <= datetime.strptime(end_date, "%Y-%m-%d"))

        nav_data = nav_query.order_by(Nav.nav_date).all()

        if not nav_data:
            return []

        # 获取指数数据
        if index_code in index_data_map and index_data_map[index_code]:
            index_data = index_data_map[index_code]
        else:
            from app.services.tushare_service import TushareIndexService
            tushare_service = TushareIndexService(db)
            index_data = tushare_service.get_index_data(
                index_code,
                start_date or (nav_data[0].nav_date - timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date or nav_data[-1].nav_date.strftime("%Y-%m-%d")
            )

        if not index_data:
            return []

        # 计算周度累计超额曲线
        quant_service = QuantitativeService(db)
        excess_curve = quant_service.calculate_weekly_excess_curve(
            nav_data, index_data, fund_code, start_date, end_date
        )

        return excess_curve

    except HTTPException:
        raise
    except Exception as e:
        print(f"计算周度超额曲线失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))