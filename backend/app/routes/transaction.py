"""
交易分析模块API路由
Transaction Analysis Module Routes
"""

import os
import pandas as pd
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_, or_
from datetime import date, datetime, timedelta
import io
import traceback
from decimal import Decimal

from app.database import get_db
from app.models import Transaction, DateConverter, Fund, Strategy, Nav, Client
from pydantic import BaseModel

router = APIRouter(prefix="/api/transaction", tags=["交易分析"])


class TransactionUploadResponse(BaseModel):
    """交易数据上传响应"""
    success_count: int = 0
    failed_count: int = 0
    total_count: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    message: str = ""


class TransactionClientSummary(BaseModel):
    """交易客户汇总信息"""
    group_id: str
    client_name: Optional[str] = None
    transaction_count: int = 0
    total_amount: float = 0
    total_fee: float = 0
    first_transaction_date: Optional[date] = None
    last_transaction_date: Optional[date] = None
    fund_count: int = 0  # 涉及基金数量
    net_amount: float = 0  # 净交易金额（买入为正，赎回为负）


class TransactionDetail(BaseModel):
    """交易详细信息"""
    id: int
    group_id: str
    client_name: Optional[str]
    fund_name: Optional[str]
    transaction_type: str
    confirmed_date: date
    confirmed_shares: Optional[float]
    confirmed_amount: Optional[float]
    transaction_fee: Optional[float]
    product_code: Optional[str]
    product_name: Optional[str]


class TransactionListResponse(BaseModel):
    """交易列表响应"""
    data: List[TransactionDetail]
    total: int = 0
    page: int = 1
    page_size: int = 20


class ProductHoldings(BaseModel):
    """产品持仓信息"""
    product_code: str
    product_name: Optional[str]
    fund_name: Optional[str]  # 基金名称（产品简称）
    # 策略信息
    main_strategy: Optional[str] = None  # 大类策略
    sub_strategy: Optional[str] = None   # 细分策略
    is_qd_product: bool = False         # 是否QD产品
    # 金额计算
    total_buy_amount: float = 0         # 买入金额
    total_sell_amount: float = 0        # 赎回金额
    total_dividend_amount: float = 0    # 分红金额
    # 持仓计算
    total_buy_shares: float = 0         # 累计申购份额
    total_sell_shares: float = 0        # 累计赎回份额
    current_shares: float = 0           # 当前持仓份额
    # 时间信息
    first_buy_date: Optional[date] = None  # 首次买入日期
    last_transaction_date: Optional[date] = None  # 最后交易日期
    # 净值和收益信息
    latest_nav: Optional[float] = None     # 最新单位净值
    nav_date: Optional[date] = None        # 净值日期
    current_market_value: float = 0        # 当前市值
    total_pnl: float = 0                  # 持有盈亏
    return_rate: float = 0                # 持有收益率
    # 持有状态
    holding_status: str = "持有中"         # 持有状态：持有中、部分赎回
    # 交易记录
    transactions: List[TransactionDetail] = []


class TransactionAnalysisResponse(BaseModel):
    """交易分析响应"""
    report_date: str  # 报告日期 yy-mm-dd
    client_info: dict
    # 按持仓状态分类
    current_holdings: List[ProductHoldings] = []  # 当前持仓产品
    cleared_products: List[ProductHoldings] = []  # 已清仓产品
    # 汇总统计
    total_products: int = 0
    current_holding_products: int = 0
    cleared_products_count: int = 0
    # 新增汇总统计数据
    total_investment_amount: float = 0      # 投资总额
    total_redemption_amount: float = 0      # 赎回总额  
    current_total_market_value: float = 0   # 当前持仓市值
    total_dividend_income: float = 0        # 总现金分红
    cumulative_pnl: float = 0              # 累计盈亏
    cumulative_return_rate: float = 0       # 累计收益率


# 支持的Excel文件列名映射（中英文对照）
COLUMN_MAPPING = {
    '集团号': 'group_id',
    '客户遮蔽姓名': 'client_name',
    '基金名称': 'fund_name',
    '交易类型名称': 'transaction_type',
    '交易确认日期': 'confirmed_date',
    '确认份额': 'confirmed_shares',
    '确认金额': 'confirmed_amount',
    '手续费': 'transaction_fee',
    '产品代码': 'product_code',
    '产品名称': 'product_name',
    # 英文字段名也支持直接映射
    'group_id': 'group_id',
    'client_name': 'client_name',
    'fund_name': 'fund_name',
    'transaction_type': 'transaction_type',
    'confirmed_date': 'confirmed_date',
    'confirmed_shares': 'confirmed_shares',
    'confirmed_amount': 'confirmed_amount',
    'transaction_fee': 'transaction_fee',
    'product_code': 'product_code',
    'product_name': 'product_name',
}


def parse_excel_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    解析Excel文件为DataFrame
    """
    try:
        # 尝试读取Excel文件
        if filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
        elif filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(file_content), engine='xlrd')
        else:
            raise ValueError(f"不支持的文件格式: {filename}")
        
        return df
    except Exception as e:
        raise ValueError(f"文件解析失败: {str(e)}")


def validate_and_transform_data(df: pd.DataFrame) -> tuple[List[dict], List[str]]:
    """
    验证并转换DataFrame数据为Transaction模型数据
    返回: (有效数据列表, 错误信息列表)
    """
    valid_data = []
    errors = []
    
    if df.empty:
        errors.append("Excel文件为空或无有效数据")
        return valid_data, errors
    
    # 检查必需列是否存在
    df_columns = df.columns.tolist()
    required_chinese_columns = ['集团号', '交易类型名称', '交易确认日期']
    
    # 映射列名
    mapped_columns = {}
    for col in df_columns:
        if col in COLUMN_MAPPING:
            mapped_columns[col] = COLUMN_MAPPING[col]
    
    if not mapped_columns:
        errors.append("Excel文件中未找到任何有效列")
        return valid_data, errors
    
    # 检查必需字段
    required_fields = ['group_id', 'transaction_type', 'confirmed_date']
    missing_required = []
    for req_field in required_fields:
        if req_field not in mapped_columns.values():
            missing_required.append(req_field)
    
    if missing_required:
        chinese_names = {'group_id': '集团号', 'transaction_type': '交易类型名称', 'confirmed_date': '交易确认日期'}
        missing_chinese = [chinese_names.get(field, field) for field in missing_required]
        errors.append(f"缺少必需列: {', '.join(missing_chinese)}")
        return valid_data, errors
    
    # 重命名列
    rename_dict = {old_col: new_col for old_col, new_col in mapped_columns.items()}
    df_renamed = df.rename(columns=rename_dict)
    
    # 逐行处理数据
    for index, row in df_renamed.iterrows():
        row_data = {}
        row_errors = []
        
        try:
            # 处理集团号
            group_id = row.get('group_id')
            if pd.isna(group_id) or group_id == '':
                row_errors.append(f"第{index+2}行: 集团号不能为空")
            else:
                row_data['group_id'] = DateConverter.format_group_id(str(group_id))
            
            # 处理交易类型
            transaction_type = row.get('transaction_type')
            if pd.isna(transaction_type) or transaction_type == '':
                row_errors.append(f"第{index+2}行: 交易类型名称不能为空")
            else:
                row_data['transaction_type'] = str(transaction_type).strip()
            
            # 处理确认日期
            confirmed_date = row.get('confirmed_date')
            if pd.isna(confirmed_date):
                row_errors.append(f"第{index+2}行: 交易确认日期不能为空")
            else:
                try:
                    if isinstance(confirmed_date, pd.Timestamp):
                        row_data['confirmed_date'] = confirmed_date.date()
                    else:
                        row_data['confirmed_date'] = DateConverter.convert_date_string(str(confirmed_date))
                except ValueError as e:
                    row_errors.append(f"第{index+2}行: 交易确认日期格式错误 - {str(e)}")
            
            # 处理可选字段
            optional_string_fields = ['client_name', 'fund_name', 'product_code', 'product_name']
            for field in optional_string_fields:
                value = row.get(field)
                if not pd.isna(value) and value != '':
                    row_data[field] = str(value).strip()
            
            # 处理数值字段
            numeric_fields = ['confirmed_shares', 'confirmed_amount', 'transaction_fee']
            for field in numeric_fields:
                value = row.get(field)
                if not pd.isna(value) and value != '':
                    try:
                        row_data[field] = float(value)
                    except (ValueError, TypeError):
                        row_errors.append(f"第{index+2}行: {field}必须为有效数字")
            
            # 如果没有错误，添加到有效数据列表
            if not row_errors:
                # 使用模型验证
                is_valid, validation_errors = Transaction.validate_transaction_data(row_data)
                if is_valid:
                    valid_data.append(row_data)
                else:
                    errors.extend([f"第{index+2}行: {error}" for error in validation_errors])
            else:
                errors.extend(row_errors)
                
        except Exception as e:
            errors.append(f"第{index+2}行: 数据处理异常 - {str(e)}")
    
    return valid_data, errors


@router.post("/upload", response_model=TransactionUploadResponse)
async def upload_transactions(
    files: List[UploadFile] = File(...),
    override_existing: bool = Query(False, description="是否覆盖已存在的数据"),
    db: Session = Depends(get_db)
):
    """
    上传交易数据Excel文件
    支持批量上传多个文件
    """
    response = TransactionUploadResponse()
    
    if not files:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")
    
    try:
        all_valid_data = []
        all_errors = []
        
        # 处理每个文件
        for file in files:
            if not file.filename.endswith(('.xlsx', '.xls')):
                all_errors.append(f"文件 {file.filename}: 不支持的文件格式，请上传Excel文件")
                continue
            
            try:
                # 读取文件内容
                file_content = await file.read()
                
                # 解析Excel文件
                df = parse_excel_file(file_content, file.filename)
                
                # 验证并转换数据
                valid_data, file_errors = validate_and_transform_data(df)
                
                all_valid_data.extend(valid_data)
                if file_errors:
                    all_errors.extend([f"文件 {file.filename}: {error}" for error in file_errors])
                    
            except Exception as e:
                all_errors.append(f"文件 {file.filename}: 处理失败 - {str(e)}")
        
        response.total_count = len(all_valid_data)
        response.errors = all_errors
        
        if not all_valid_data:
            response.message = "没有有效的交易数据可以导入"
            return response
        
        # 保存到数据库
        success_count = 0
        failed_count = 0
        
        for data in all_valid_data:
            try:
                # 检查是否存在相同记录 - 修复重复检测逻辑，增加更多唯一标识字段
                existing = None
                if not override_existing:
                    # 构建更完整的重复检测条件
                    conditions = [
                        Transaction.group_id == data['group_id'],
                        Transaction.transaction_type == data['transaction_type'],
                        Transaction.confirmed_date == data['confirmed_date']
                    ]
                    
                    # 添加确认金额条件（处理None值）
                    confirmed_amount = data.get('confirmed_amount')
                    if confirmed_amount is not None:
                        conditions.append(Transaction.confirmed_amount == confirmed_amount)
                    else:
                        conditions.append(Transaction.confirmed_amount.is_(None))
                    
                    # 添加确认份额条件（处理None值）
                    confirmed_shares = data.get('confirmed_shares')
                    if confirmed_shares is not None:
                        conditions.append(Transaction.confirmed_shares == confirmed_shares)
                    else:
                        conditions.append(Transaction.confirmed_shares.is_(None))
                    
                    # 添加产品标识条件（优先使用product_code，其次fund_name）
                    product_code = data.get('product_code')
                    fund_name = data.get('fund_name')
                    if product_code:
                        conditions.append(Transaction.product_code == product_code)
                    elif fund_name:
                        conditions.append(Transaction.fund_name == fund_name)
                    
                    existing = db.query(Transaction).filter(and_(*conditions)).first()
                
                if existing and not override_existing:
                    # 跳过已存在的记录
                    continue
                
                if existing and override_existing:
                    # 更新现有记录
                    for key, value in data.items():
                        setattr(existing, key, value)
                    db.flush()
                else:
                    # 创建新记录
                    transaction = Transaction(**data)
                    db.add(transaction)
                    db.flush()
                
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                response.errors.append(f"保存交易记录失败: {str(e)}")
        
        # 提交事务
        db.commit()
        
        response.success_count = success_count
        response.failed_count = failed_count
        response.message = f"成功导入 {success_count} 条交易记录，失败 {failed_count} 条"
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"交易数据上传失败: {str(e)}")


@router.get("/clients", response_model=List[TransactionClientSummary])
async def get_transaction_clients(
    search: Optional[str] = Query(None, description="搜索集团号或客户姓名"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
):
    """
    获取交易客户列表
    按客户聚合显示交易统计信息
    """
    try:
        # 构建查询条件
        query = db.query(
            Transaction.group_id,
            func.max(Transaction.client_name).label('client_name'),
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.confirmed_amount).label('total_amount'),
            func.sum(Transaction.transaction_fee).label('total_fee'),
            func.min(Transaction.confirmed_date).label('first_transaction_date'),
            func.max(Transaction.confirmed_date).label('last_transaction_date'),
            func.count(func.distinct(Transaction.fund_name)).label('fund_count')
        )
        
        # 添加搜索条件
        if search:
            query = query.filter(
                or_(
                    Transaction.group_id.like(f"%{search}%"),
                    Transaction.client_name.like(f"%{search}%")
                )
            )
        
        # 添加日期范围过滤
        if start_date:
            query = query.filter(Transaction.confirmed_date >= start_date)
        if end_date:
            query = query.filter(Transaction.confirmed_date <= end_date)
        
        # 分组
        query = query.group_by(Transaction.group_id)
        
        # 排序（按总交易金额降序）
        query = query.order_by(func.sum(Transaction.confirmed_amount).desc())
        
        # 分页
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()
        
        # 转换为响应格式
        clients = []
        for result in results:
            # 计算净交易金额（买入为正，赎回为负的假设）
            # 这里需要根据实际业务逻辑调整
            net_amount = float(result.total_amount or 0)
            
            client = TransactionClientSummary(
                group_id=result.group_id,
                client_name=result.client_name,
                transaction_count=result.transaction_count,
                total_amount=float(result.total_amount or 0),
                total_fee=float(result.total_fee or 0),
                first_transaction_date=result.first_transaction_date,
                last_transaction_date=result.last_transaction_date,
                fund_count=result.fund_count,
                net_amount=net_amount
            )
            clients.append(client)
        
        return clients
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易客户列表失败: {str(e)}")


@router.get("/clients/{group_id}/transactions", response_model=TransactionListResponse)
async def get_client_transactions(
    group_id: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    transaction_type: Optional[str] = Query(None, description="交易类型筛选"),
    fund_name: Optional[str] = Query(None, description="基金名称筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
):
    """
    获取指定客户的交易记录详情
    """
    try:
        query = db.query(Transaction).filter(Transaction.group_id == group_id)
        
        # 添加过滤条件
        if start_date:
            query = query.filter(Transaction.confirmed_date >= start_date)
        if end_date:
            query = query.filter(Transaction.confirmed_date <= end_date)
        if transaction_type:
            query = query.filter(Transaction.transaction_type.like(f"%{transaction_type}%"))
        if fund_name:
            query = query.filter(Transaction.fund_name.like(f"%{fund_name}%"))
        
        # 获取总数
        total = query.count()
        
        # 排序和分页
        query = query.order_by(Transaction.confirmed_date.desc())
        offset = (page - 1) * page_size
        transactions = query.offset(offset).limit(page_size).all()
        
        # 转换为响应格式
        transaction_details = []
        for t in transactions:
            detail = TransactionDetail(
                id=t.id,
                group_id=t.group_id,
                client_name=t.client_name,
                fund_name=t.fund_name,
                transaction_type=t.transaction_type,
                confirmed_date=t.confirmed_date,
                confirmed_shares=float(t.confirmed_shares) if t.confirmed_shares else None,
                confirmed_amount=float(t.confirmed_amount) if t.confirmed_amount else None,
                transaction_fee=float(t.transaction_fee) if t.transaction_fee else None,
                product_code=t.product_code,
                product_name=t.product_name
            )
            transaction_details.append(detail)
        
        return TransactionListResponse(
            data=transaction_details,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户交易记录失败: {str(e)}")


@router.delete("/clients/{group_id}")
async def delete_client_transactions(
    group_id: str,
    db: Session = Depends(get_db)
):
    """
    删除指定客户的所有交易记录
    """
    try:
        deleted_count = db.query(Transaction).filter(Transaction.group_id == group_id).count()
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="未找到该客户的交易记录")
        
        db.query(Transaction).filter(Transaction.group_id == group_id).delete()
        db.commit()
        
        return {
            "success": True,
            "message": f"成功删除客户 {group_id} 的 {deleted_count} 条交易记录"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除交易记录失败: {str(e)}")


@router.get("/stats")
async def get_transaction_stats(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取交易统计信息
    """
    try:
        query = db.query(Transaction)
        
        # 添加日期范围过滤
        if start_date:
            query = query.filter(Transaction.confirmed_date >= start_date)
        if end_date:
            query = query.filter(Transaction.confirmed_date <= end_date)
        
        # 基础统计
        total_transactions = query.count()
        total_clients = query.with_entities(func.count(func.distinct(Transaction.group_id))).scalar()
        total_amount = query.with_entities(func.sum(Transaction.confirmed_amount)).scalar() or 0
        total_fee = query.with_entities(func.sum(Transaction.transaction_fee)).scalar() or 0
        
        # 按交易类型统计
        type_stats = query.with_entities(
            Transaction.transaction_type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.confirmed_amount).label('amount')
        ).group_by(Transaction.transaction_type).all()
        
        return {
            "total_transactions": total_transactions,
            "total_clients": total_clients,
            "total_amount": float(total_amount),
            "total_fee": float(total_fee),
            "type_statistics": [
                {
                    "transaction_type": stat.transaction_type,
                    "count": stat.count,
                    "amount": float(stat.amount or 0)
                }
                for stat in type_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易统计失败: {str(e)}")


@router.get("/clients/{group_id}/analysis", response_model=TransactionAnalysisResponse)
async def get_client_transaction_analysis(
    group_id: str,
    db: Session = Depends(get_db)
):
    """
    获取客户的详细交易分析
    包括持仓分类、策略分组、收益计算等
    """
    try:
        
        # 获取客户的所有交易记录
        transactions = db.query(Transaction).filter(
            Transaction.group_id == group_id
        ).order_by(Transaction.confirmed_date.asc()).all()
        
        if not transactions:
            raise HTTPException(status_code=404, detail="未找到该客户的交易记录")
        
        # 获取客户基本信息
        client_info = {
            "group_id": group_id,
            "client_name": transactions[0].client_name,
            "total_transactions": len(transactions)
        }
        
        # 按产品分组交易记录
        product_transactions = {}
        for t in transactions:
            key = t.product_code or t.fund_name or "未知产品"
            if key not in product_transactions:
                product_transactions[key] = []
            product_transactions[key].append(t)
        
        # 计算每个产品的持仓情况
        current_holdings = []
        cleared_products = []
        
        for product_code, product_trans in product_transactions.items():
            # 计算买入和卖出份额以及金额
            total_buy_shares = 0
            total_sell_shares = 0
            total_buy_amount = 0
            total_sell_amount = 0
            total_dividend_amount = 0
            first_buy_date = None
            last_transaction_date = None
            
            transaction_details = []
            
            for t in product_trans:
                # 转换交易记录为详情格式
                detail = TransactionDetail(
                    id=t.id,
                    group_id=t.group_id,
                    client_name=t.client_name,
                    fund_name=t.fund_name,
                    transaction_type=t.transaction_type,
                    confirmed_date=t.confirmed_date,
                    confirmed_shares=float(t.confirmed_shares) if t.confirmed_shares else None,
                    confirmed_amount=float(t.confirmed_amount) if t.confirmed_amount else None,
                    transaction_fee=float(t.transaction_fee) if t.transaction_fee else None,
                    product_code=t.product_code,
                    product_name=t.product_name
                )
                transaction_details.append(detail)
                
                # 计算份额和金额（根据交易类型判断买入还是卖出）
                transaction_type = t.transaction_type.lower()
                
                if t.confirmed_shares:
                    shares = float(t.confirmed_shares)
                    
                    # 份额增加的交易类型
                    if any(keyword in transaction_type for keyword in ['申购', '买入', '认购', '认购结果', '增持', '强制调增', '强行调增']):
                        total_buy_shares += shares
                        if first_buy_date is None or t.confirmed_date < first_buy_date:
                            first_buy_date = t.confirmed_date
                    # 份额减少的交易类型  
                    elif any(keyword in transaction_type for keyword in ['赎回', '卖出', '减持', '强制调减', '强行调减', '强制赎回']):
                        total_sell_shares += shares
                
                # 计算金额
                if t.confirmed_amount:
                    amount = float(t.confirmed_amount)
                    
                    # 资金流入（买入）
                    if any(keyword in transaction_type for keyword in ['申购', '买入', '认购', '认购结果', '增持']):
                        total_buy_amount += amount
                    # 资金流出（赎回）  
                    elif any(keyword in transaction_type for keyword in ['赎回', '卖出', '减持', '强制赎回']):
                        total_sell_amount += amount
                    # 现金分红（收入）
                    elif '分红' in transaction_type:
                        total_dividend_amount += amount
                    # 强制调增/调减和强行调增/调减不涉及资金流动，只调整份额
                
                # 更新最后交易日期
                if last_transaction_date is None or t.confirmed_date > last_transaction_date:
                    last_transaction_date = t.confirmed_date
            
            # 计算当前持有份额
            current_shares = total_buy_shares - total_sell_shares
            
            # 处理浮点数精度问题：如果份额小于0.01，视为0
            if abs(current_shares) < 0.01:
                current_shares = 0
            
            # 获取策略信息（通过产品代码查找）
            main_strategy = None
            sub_strategy = None
            is_qd_product = False
            latest_nav = None
            nav_date = None
            
            if product_code and product_code != "未知产品":
                # 尝试多种方式查找基金策略信息
                fund = None
                nav_fund_code = product_code  # 用于查找净值的基金代码
                
                # 首先尝试直接使用产品代码查找
                fund = db.query(Fund).filter(Fund.fund_code == product_code).first()
                
                # 如果没找到，尝试通过产品名称模糊匹配
                if not fund:
                    # 使用第一个交易记录的基金名称或产品名称进行匹配
                    sample_transaction = transaction_details[0] if transaction_details else None
                    if sample_transaction:
                        search_name = sample_transaction.fund_name or sample_transaction.product_name
                        if search_name:
                            # 模糊匹配基金名称
                            fund = db.query(Fund).filter(Fund.fund_name.contains(search_name.replace('龙舟-', '').strip())).first()
                            if fund:
                                nav_fund_code = fund.fund_code  # 使用匹配到的基金代码查找净值
                
                if fund and fund.strategy:
                    main_strategy = fund.strategy.main_strategy
                    sub_strategy = fund.strategy.sub_strategy
                    is_qd_product = fund.strategy.is_qd_product if hasattr(fund.strategy, 'is_qd_product') else False
                
                # 获取最新净值和净值日期（使用正确的基金代码）
                latest_nav_record = db.query(Nav).filter(
                    Nav.fund_code == nav_fund_code
                ).order_by(Nav.nav_date.desc()).first()
                
                if latest_nav_record:
                    latest_nav = float(latest_nav_record.unit_nav)
                    nav_date = latest_nav_record.nav_date
            
            # 计算市值和收益
            current_market_value = current_shares * (latest_nav or 0) if latest_nav else 0
            
            # 持有盈亏 = 净值*持有份额 + 赎回金额 + 分红金额 - 买入金额
            total_pnl = current_market_value + total_sell_amount + total_dividend_amount - total_buy_amount
            
            # 持有收益率 = 持有盈亏 / 买入金额 (避免除零)
            return_rate = (total_pnl / total_buy_amount * 100) if total_buy_amount > 0 else 0
            
            # 判断持有状态
            holding_status = "持有中"
            if total_sell_amount > 0 and total_sell_amount < total_buy_amount:
                holding_status = "部分赎回"
            elif current_shares <= 0:
                holding_status = "已清仓"
            
            # 创建产品持仓信息
            holding = ProductHoldings(
                product_code=product_code,
                product_name=product_trans[0].product_name,
                fund_name=product_trans[0].fund_name,
                main_strategy=main_strategy,
                sub_strategy=sub_strategy,
                is_qd_product=is_qd_product,
                total_buy_amount=total_buy_amount,
                total_sell_amount=total_sell_amount,
                total_dividend_amount=total_dividend_amount,
                total_buy_shares=total_buy_shares,
                total_sell_shares=total_sell_shares,
                current_shares=current_shares,
                first_buy_date=first_buy_date,
                last_transaction_date=last_transaction_date,
                latest_nav=latest_nav,
                nav_date=nav_date,
                current_market_value=current_market_value,
                total_pnl=total_pnl,
                return_rate=return_rate,
                holding_status=holding_status,
                transactions=transaction_details
            )
            
            # 根据持仓状态分类 - 只有持有份额大于0的才算当前持仓
            if current_shares > 0:
                current_holdings.append(holding)
            else:
                # 持仓份额为0或负数的都算已清仓产品
                cleared_products.append(holding)
        
        # 对当前持仓按策略分组和排序
        def get_strategy_sort_key(holding):
            """获取策略排序键"""
            main_strategy = holding.main_strategy or "其他"
            sub_strategy = holding.sub_strategy or "其他"
            
            # 主策略排序
            main_strategy_order = {"成长策略": 1, "固收策略": 2, "宏观策略": 3, "其他": 4}
            main_order = main_strategy_order.get(main_strategy, 4)
            
            # 细分策略排序（针对成长策略）
            if main_strategy == "成长策略":
                sub_strategy_order = {
                    "主观多头": 1, "股票多头": 2, "股票多空": 3, 
                    "量化多头": 4, "其他": 5
                }
                sub_order = sub_strategy_order.get(sub_strategy, 5)
            else:
                sub_order = 1
            
            # 买入时间排序（越早越前）
            buy_date_order = holding.first_buy_date or date.today()
            
            return (main_order, sub_order, buy_date_order)
        
        # 排序当前持仓
        current_holdings.sort(key=get_strategy_sort_key)
        
        # 排序已清仓产品（按产品名称）
        cleared_products.sort(key=lambda x: x.product_name or x.product_code or "")
        
        # 生成报告日期
        today = datetime.now()
        report_date = today.strftime("%y-%m-%d")
        
        # 计算汇总统计数据
        all_products = current_holdings + cleared_products
        
        # 投资总额 = 所有产品的买入金额总和
        total_investment_amount = sum(product.total_buy_amount for product in all_products)
        
        # 赎回总额 = 所有产品的赎回金额总和  
        total_redemption_amount = sum(product.total_sell_amount for product in all_products)
        
        # 当前持仓市值 = 所有当前持仓产品的市值总和
        current_total_market_value = sum(product.current_market_value for product in current_holdings)
        
        # 总现金分红 = 所有产品的分红金额总和
        total_dividend_income = sum(product.total_dividend_amount for product in all_products)
        
        # 累计盈亏 = 所有产品（当前持仓+已清仓）的盈亏总和
        cumulative_pnl = sum(product.total_pnl for product in all_products)
        
        # 累计收益率 = 累计盈亏 / 投资总额
        cumulative_return_rate = (cumulative_pnl / total_investment_amount * 100) if total_investment_amount > 0 else 0
        
        return TransactionAnalysisResponse(
            report_date=report_date,
            client_info=client_info,
            current_holdings=current_holdings,
            cleared_products=cleared_products,
            total_products=len(product_transactions),
            current_holding_products=len(current_holdings),
            cleared_products_count=len(cleared_products),
            # 新增汇总统计数据
            total_investment_amount=total_investment_amount,
            total_redemption_amount=total_redemption_amount,
            current_total_market_value=current_total_market_value,
            total_dividend_income=total_dividend_income,
            cumulative_pnl=cumulative_pnl,
            cumulative_return_rate=cumulative_return_rate
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易分析失败: {str(e)}")


# 阶段收益分析相关模型
class MonthlyProfitData(BaseModel):
    """月度收益数据"""
    year_month: str  # 年月，格式：2024-01
    month_start_value: float = 0  # 月初市值
    month_end_value: float = 0  # 月末市值
    net_cashflow: float = 0  # 净现金流（申购-赎回）
    monthly_return: float = 0  # 月度绝对收益
    cumulative_return: float = 0  # 累计绝对收益
    dividend_amount: float = 0  # 当月分红金额


class PeriodProfitAnalysis(BaseModel):
    """时间段收益分析数据"""
    product_code: str
    product_name: Optional[str] = None
    fund_name: Optional[str] = None
    main_strategy: Optional[str] = None
    sub_strategy: Optional[str] = None
    start_market_value: float = 0  # 期初市值
    end_market_value: float = 0  # 期末市值
    period_cashflow: float = 0  # 期间净现金流
    period_return: float = 0  # 期间收益
    return_contribution: float = 0  # 收益占比


class PeriodAnalysisSummary(BaseModel):
    """时间段分析摘要"""
    start_date: date
    end_date: date
    total_start_value: float = 0
    total_end_value: float = 0
    total_return: float = 0
    total_return_rate: float = 0
    product_count: int = 0


class StageAnalysisResponse(BaseModel):
    """阶段收益分析响应"""
    client_info: dict
    monthly_trend: List[MonthlyProfitData] = []
    period_analysis: Optional[PeriodAnalysisSummary] = None
    product_details: List[PeriodProfitAnalysis] = []


@router.get("/clients/{group_id}/monthly-profit-trend", response_model=StageAnalysisResponse)
async def get_client_monthly_profit_trend(
    group_id: str,
    db: Session = Depends(get_db)
):
    """
    获取客户的月度绝对收益趋势数据
    从首次交易至今的每月收益曲线
    """
    try:
        # 获取客户的所有交易记录
        transactions = db.query(Transaction).filter(
            Transaction.group_id == group_id
        ).order_by(Transaction.confirmed_date.asc()).all()
        
        if not transactions:
            raise HTTPException(status_code=404, detail="未找到该客户的交易记录")
        
        # 获取客户基本信息
        client_info = {
            "group_id": group_id,
            "client_name": transactions[0].client_name,
            "total_transactions": len(transactions)
        }
        
        # 按产品分组交易记录
        product_transactions = {}
        for t in transactions:
            key = t.product_code or t.fund_name or "未知产品"
            if key not in product_transactions:
                product_transactions[key] = []
            product_transactions[key].append(t)
        
        # 获取时间范围（从第一笔交易到现在）
        first_transaction_date = min(t.confirmed_date for t in transactions)
        last_transaction_date = max(t.confirmed_date for t in transactions)
        current_date = datetime.now().date()
        
        # 生成月度时间序列
        monthly_data = {}
        current_month = first_transaction_date.replace(day=1)
        end_month = current_date.replace(day=1)
        
        while current_month <= end_month:
            month_key = current_month.strftime("%Y-%m")
            monthly_data[month_key] = MonthlyProfitData(year_month=month_key)
            
            # 移动到下个月
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        # 计算每个月的收益数据
        for month_key in monthly_data.keys():
            year, month = map(int, month_key.split('-'))
            month_start = date(year, month, 1)
            
            # 计算下个月第一天
            if month == 12:
                month_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(year, month + 1, 1) - timedelta(days=1)
            
            month_start_value = 0
            month_end_value = 0
            net_cashflow = 0
            dividend_amount = 0
            
            # 计算每个产品在这个月的绝对收益
            monthly_return = 0
            
            for product_code, product_trans in product_transactions.items():
                if product_code == "未知产品":
                    continue
                    
                # 计算月初持有份额
                start_shares = 0
                for t in product_trans:
                    if t.confirmed_date < month_start and t.confirmed_shares:
                        shares = float(t.confirmed_shares)
                        transaction_type = t.transaction_type.lower()
                        
                        if any(keyword in transaction_type for keyword in ['申购', '买入', '认购', '认购结果', '增持', '强制调增', '强行调增']):
                            start_shares += shares
                        elif any(keyword in transaction_type for keyword in ['赎回', '卖出', '减持', '强制调减', '强行调减', '强制赎回']):
                            start_shares -= shares
                
                start_shares = max(0, start_shares)
                
                # 获取月初净值
                start_nav = None
                if start_shares > 0:
                    start_nav_record = db.query(Nav).filter(
                        Nav.fund_code == product_code,
                        Nav.nav_date <= month_start
                    ).order_by(Nav.nav_date.desc()).first()
                    if start_nav_record:
                        start_nav = float(start_nav_record.unit_nav)
                
                # 月初市值
                start_value = (start_shares * start_nav) if (start_nav and start_shares > 0) else 0
                month_start_value += start_value
                
                # 处理月内交易
                current_shares = start_shares
                product_return = 0
                
                # 按时间排序处理月内交易
                month_transactions = [t for t in product_trans if month_start <= t.confirmed_date <= month_end]
                month_transactions.sort(key=lambda x: x.confirmed_date)
                
                for t in month_transactions:
                    transaction_type = t.transaction_type.lower()
                    
                    if t.confirmed_shares:
                        shares = float(t.confirmed_shares)
                        
                        # 获取交易日净值
                        trade_nav_record = db.query(Nav).filter(
                            Nav.fund_code == product_code,
                            Nav.nav_date <= t.confirmed_date
                        ).order_by(Nav.nav_date.desc()).first()
                        
                        trade_nav = float(trade_nav_record.unit_nav) if trade_nav_record else None
                        
                        if any(keyword in transaction_type for keyword in ['申购', '买入', '认购', '认购结果', '增持', '强制调增', '强行调增']):
                            # 申购：新增持仓，从申购日开始计算收益
                            current_shares += shares
                            if t.confirmed_amount:
                                net_cashflow += float(t.confirmed_amount)
                                
                        elif any(keyword in transaction_type for keyword in ['赎回', '卖出', '减持', '强制调减', '强行调减', '强制赎回']):
                            # 赎回：计算被赎回份额从月初到赎回日的收益
                            if trade_nav and start_nav and shares > 0:
                                redemption_return = shares * (trade_nav - start_nav)
                                product_return += redemption_return
                            
                            current_shares -= shares
                            if t.confirmed_amount:
                                net_cashflow -= float(t.confirmed_amount)
                    
                    # 计算分红
                    if '分红' in transaction_type and t.confirmed_amount:
                        dividend_amount += float(t.confirmed_amount)
                
                # 计算剩余持仓的月度收益（月初持仓+月内新增持仓的月末收益）
                current_shares = max(0, current_shares)
                if current_shares > 0:
                    end_nav_record = db.query(Nav).filter(
                        Nav.fund_code == product_code,
                        Nav.nav_date <= month_end
                    ).order_by(Nav.nav_date.desc()).first()
                    
                    if end_nav_record:
                        end_nav = float(end_nav_record.unit_nav)
                        end_value = current_shares * end_nav
                        month_end_value += end_value
                        
                        # 存量持仓收益：月初持仓的净值增长
                        if start_nav and start_shares > 0:
                            existing_shares_return = min(start_shares, current_shares) * (end_nav - start_nav)
                            product_return += existing_shares_return
                        
                        # 新增持仓收益：需要分别计算每笔申购的收益
                        new_shares = max(0, current_shares - start_shares)
                        if new_shares > 0:
                            # 简化处理：假设新增持仓在月中间申购，使用平均收益率
                            avg_purchase_nav = (start_nav + end_nav) / 2 if start_nav else end_nav
                            new_shares_return = new_shares * (end_nav - avg_purchase_nav)
                            product_return += new_shares_return
                
                monthly_return += product_return
            
            monthly_data[month_key] = MonthlyProfitData(
                year_month=month_key,
                month_start_value=round(month_start_value, 2),
                month_end_value=round(month_end_value, 2),
                net_cashflow=round(net_cashflow, 2),
                monthly_return=round(monthly_return, 2),
                dividend_amount=round(dividend_amount, 2)
            )
        
        # 转换为列表并按时间排序
        monthly_trend = list(monthly_data.values())
        monthly_trend.sort(key=lambda x: x.year_month)
        
        # 计算累计绝对收益
        cumulative_return = 0
        for month_data in monthly_trend:
            cumulative_return += month_data.monthly_return
            month_data.cumulative_return = round(cumulative_return, 2)
        
        return StageAnalysisResponse(
            client_info=client_info,
            monthly_trend=monthly_trend,
            period_analysis=None,
            product_details=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取月度收益趋势失败: {str(e)}")


@router.get("/clients/{group_id}/period-profit-analysis", response_model=StageAnalysisResponse)
async def get_client_period_profit_analysis(
    group_id: str,
    start_date: date = Query(..., description="分析开始日期"),
    end_date: date = Query(..., description="分析结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取客户指定时间段的产品收益明细分析
    """
    try:
        # 验证日期范围
        if start_date >= end_date:
            raise HTTPException(status_code=400, detail="开始日期必须小于结束日期")
        
        # 获取客户的所有交易记录
        transactions = db.query(Transaction).filter(
            Transaction.group_id == group_id
        ).order_by(Transaction.confirmed_date.asc()).all()
        
        if not transactions:
            raise HTTPException(status_code=404, detail="未找到该客户的交易记录")
        
        # 获取客户基本信息
        client_info = {
            "group_id": group_id,
            "client_name": transactions[0].client_name,
            "analysis_period": f"{start_date} 至 {end_date}"
        }
        
        # 按产品分组交易记录
        product_transactions = {}
        for t in transactions:
            key = t.product_code or t.fund_name or "未知产品"
            if key not in product_transactions:
                product_transactions[key] = []
            product_transactions[key].append(t)
        
        # 分析每个产品在指定时间段的收益
        product_details = []
        total_start_value = 0
        total_end_value = 0
        total_return = 0
        
        for product_code, product_trans in product_transactions.items():
            # 获取产品基本信息
            product_name = product_trans[0].product_name
            fund_name = product_trans[0].fund_name
            main_strategy = None
            sub_strategy = None
            
            if product_code != "未知产品":
                fund = db.query(Fund).filter(Fund.fund_code == product_code).first()
                if fund and fund.strategy:
                    main_strategy = fund.strategy.main_strategy
                    sub_strategy = fund.strategy.sub_strategy
            
            # 计算期初持有份额（start_date之前的交易）
            start_shares = 0
            for t in product_trans:
                if t.confirmed_date < start_date and t.confirmed_shares:
                    shares = float(t.confirmed_shares)
                    transaction_type = t.transaction_type.lower()
                    
                    if any(keyword in transaction_type for keyword in ['申购', '买入', '认购', '认购结果', '增持', '强制调增', '强行调增']):
                        start_shares += shares
                    elif any(keyword in transaction_type for keyword in ['赎回', '卖出', '减持', '强制调减', '强行调减', '强制赎回']):
                        start_shares -= shares
            
            # 计算期末持有份额（end_date之前的所有交易）
            end_shares = 0
            period_cashflow = 0
            
            for t in product_trans:
                if t.confirmed_date <= end_date and t.confirmed_shares:
                    shares = float(t.confirmed_shares)
                    transaction_type = t.transaction_type.lower()
                    
                    if any(keyword in transaction_type for keyword in ['申购', '买入', '认购', '认购结果', '增持', '强制调增', '强行调增']):
                        end_shares += shares
                        # 期间内的申购记为现金流出
                        if start_date <= t.confirmed_date <= end_date and t.confirmed_amount:
                            period_cashflow += float(t.confirmed_amount)
                    elif any(keyword in transaction_type for keyword in ['赎回', '卖出', '减持', '强制调减', '强行调减', '强制赎回']):
                        end_shares -= shares
                        # 期间内的赎回记为现金流入
                        if start_date <= t.confirmed_date <= end_date and t.confirmed_amount:
                            period_cashflow -= float(t.confirmed_amount)
            
            # 获取期初和期末净值
            start_nav = None
            end_nav = None
            
            if product_code != "未知产品":
                # 获取最接近开始日期的净值
                start_nav_record = db.query(Nav).filter(
                    Nav.fund_code == product_code,
                    Nav.nav_date <= start_date
                ).order_by(Nav.nav_date.desc()).first()
                
                if start_nav_record:
                    start_nav = float(start_nav_record.unit_nav)
                
                # 获取最接近结束日期的净值
                end_nav_record = db.query(Nav).filter(
                    Nav.fund_code == product_code,
                    Nav.nav_date <= end_date
                ).order_by(Nav.nav_date.desc()).first()
                
                if end_nav_record:
                    end_nav = float(end_nav_record.unit_nav)
            
            # 计算市值
            start_market_value = (start_shares * start_nav) if (start_nav and start_shares > 0) else 0
            end_market_value = (end_shares * end_nav) if (end_nav and end_shares > 0) else 0
            
            # 计算期间收益：期末市值 - 期初市值 - 期间净现金流
            period_return = end_market_value - start_market_value - period_cashflow
            
            # 只包含有持仓或有交易的产品
            if start_market_value > 0 or end_market_value > 0 or abs(period_cashflow) > 0:
                product_details.append(PeriodProfitAnalysis(
                    product_code=product_code,
                    product_name=product_name,
                    fund_name=fund_name,
                    main_strategy=main_strategy,
                    sub_strategy=sub_strategy,
                    start_market_value=round(start_market_value, 2),
                    end_market_value=round(end_market_value, 2),
                    period_cashflow=round(period_cashflow, 2),
                    period_return=round(period_return, 2),
                    return_contribution=0  # 稍后计算
                ))
                
                total_start_value += start_market_value
                total_end_value += end_market_value
                total_return += period_return
        
        # 计算收益占比
        for product in product_details:
            if total_return != 0:
                product.return_contribution = round((product.period_return / total_return * 100), 2)
        
        # 计算总收益率
        total_return_rate = (total_return / total_start_value * 100) if total_start_value > 0 else 0
        
        # 创建分析摘要
        period_analysis = PeriodAnalysisSummary(
            start_date=start_date,
            end_date=end_date,
            total_start_value=round(total_start_value, 2),
            total_end_value=round(total_end_value, 2),
            total_return=round(total_return, 2),
            total_return_rate=round(total_return_rate, 2),
            product_count=len(product_details)
        )
        
        # 按收益贡献排序
        product_details.sort(key=lambda x: x.period_return, reverse=True)
        
        return StageAnalysisResponse(
            client_info=client_info,
            monthly_trend=[],
            period_analysis=period_analysis,
            product_details=product_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间段收益分析失败: {str(e)}")