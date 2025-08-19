"""
分红管理路由
Dividend Management Routes
实现基金分红数据管理API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional
from datetime import date
from decimal import Decimal
import logging
import pandas as pd
from io import BytesIO

from ..database import get_db
from ..schemas.dividend import (
    DividendResponse, DividendListResponse, DividendUploadResponse,
    ClientDividendSummary, FundDividendHistory, DividendAnalysisRequest,
    DividendAnalysisResponse
)
from ..models import Dividend, Fund, DateConverter

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/dividend",
    tags=["分红管理"],
    responses={
        404: {"description": "资源未找到"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)


@router.post("/upload", summary="批量上传分红数据")
async def upload_dividends(
    files: List[UploadFile] = File(..., description="Excel分红文件列表"),
    override_existing: bool = Query(False, description="是否覆盖已存在数据"),
    db: Session = Depends(get_db)
):
    """
    批量上传Excel分红文件
    
    - **files**: Excel文件列表，支持.xlsx格式
    - **override_existing**: 是否覆盖已存在的分红数据
    - **返回**: 处理统计信息和错误详情
    
    Excel文件格式要求：
    - 基金代码: 基金代码
    - 分红日期: 分红发放日期(20250701或2025-07-01)
    - 每份分红: 每份分红金额
    - 除息日: 可选，除息日期
    - 登记日: 可选，登记日期
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请至少上传一个文件"
        )
    
    total_results = {
        "success_count": 0,
        "failed_count": 0,
        "updated_count": 0,
        "created_count": 0,
        "errors": [],
        "processed_files": []
    }
    
    try:
        for file in files:
            # 验证文件类型
            if not file.filename.endswith(('.xlsx', '.xls')):
                total_results["errors"].append(f"文件 {file.filename} 不是Excel格式")
                continue
            
            # 读取文件内容
            file_content = await file.read()
            
            # 处理单个文件
            result = await process_dividend_excel(file_content, file.filename, override_existing, db)
            
            # 累计统计
            total_results["success_count"] += result["success_count"]
            total_results["failed_count"] += result["failed_count"]
            total_results["updated_count"] += result["updated_count"]
            total_results["created_count"] += result["created_count"]
            total_results["errors"].extend([f"{file.filename}: {error}" for error in result["errors"]])
            
            total_results["processed_files"].append({
                "filename": file.filename,
                "success_count": result["success_count"],
                "failed_count": result["failed_count"]
            })
            
            logger.info(f"分红文件 {file.filename} 处理完成: 成功{result['success_count']}, 失败{result['failed_count']}")
        
        return {
            "success": True,
            "message": f"分红文件上传处理完成，成功{total_results['success_count']}条，失败{total_results['failed_count']}条",
            "data": total_results
        }
        
    except Exception as e:
        logger.error(f"分红文件上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


async def process_dividend_excel(file_content: bytes, filename: str, override_existing: bool, db: Session) -> dict:
    """
    处理单个分红Excel文件
    """
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
            '产品代码': 'fund_code',
            '分红日期': 'dividend_date',
            '分红发放日': 'dividend_date',
            '每份分红': 'dividend_per_share',
            '分红金额': 'dividend_per_share',
            '除息日': 'ex_dividend_date',
            '登记日': 'record_date',
            # 英文字段名（兼容性）
            'fund_code': 'fund_code',
            'dividend_date': 'dividend_date',
            'dividend_per_share': 'dividend_per_share',
            'ex_dividend_date': 'ex_dividend_date',
            'record_date': 'record_date'
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
        
        # 验证必要列
        required_columns = ['fund_code', 'dividend_date', 'dividend_per_share']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            error_msg = f"Excel文件缺少必要列: {', '.join(missing_columns)}"
            errors.append(error_msg)
            return {
                "success_count": 0,
                "failed_count": len(df) if len(df) > 0 else 1,
                "updated_count": 0,
                "created_count": 0,
                "errors": errors
            }
        
        # 处理每一行数据
        for index, row in df.iterrows():
            try:
                # 获取基本字段
                fund_code = str(row['fund_code']).strip()
                
                # 处理日期
                dividend_date_str = str(row['dividend_date']).strip()
                dividend_date = DateConverter.convert_date_string(dividend_date_str)
                
                # 处理分红金额
                dividend_per_share = Decimal(str(row['dividend_per_share']))
                
                # 处理可选日期字段
                ex_dividend_date = None
                if 'ex_dividend_date' in row and pd.notna(row['ex_dividend_date']):
                    ex_dividend_date_str = str(row['ex_dividend_date']).strip()
                    ex_dividend_date = DateConverter.convert_date_string(ex_dividend_date_str)
                
                record_date = None
                if 'record_date' in row and pd.notna(row['record_date']):
                    record_date_str = str(row['record_date']).strip()
                    record_date = DateConverter.convert_date_string(record_date_str)
                
                # 验证基金是否存在，如果不存在则自动创建
                fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()
                if not fund:
                    fund_name = f"基金_{fund_code}"  # 默认名称
                    new_fund = Fund(
                        fund_code=fund_code,
                        fund_name=fund_name
                    )
                    db.add(new_fund)
                    db.flush()
                    fund = new_fund
                    logger.info(f"自动创建基金: {fund_code} - {fund_name}")
                
                # 验证分红数据
                is_valid, error_msg = Dividend.validate_dividend_data(dividend_per_share, dividend_date)
                if not is_valid:
                    errors.append(f"第{index+2}行: {error_msg}")
                    failed_count += 1
                    continue
                
                # 检查分红是否已存在
                existing_dividend = db.query(Dividend).filter(
                    and_(
                        Dividend.fund_code == fund_code,
                        Dividend.dividend_date == dividend_date
                    )
                ).first()
                
                if existing_dividend:
                    if override_existing:
                        # 更新分红
                        existing_dividend.dividend_per_share = dividend_per_share
                        existing_dividend.ex_dividend_date = ex_dividend_date
                        existing_dividend.record_date = record_date
                        updated_count += 1
                    else:
                        errors.append(f"第{index+2}行: 分红记录已存在 ({fund_code}, {dividend_date})")
                        failed_count += 1
                        continue
                else:
                    # 创建新分红
                    new_dividend = Dividend(
                        fund_code=fund_code,
                        dividend_date=dividend_date,
                        dividend_per_share=dividend_per_share,
                        ex_dividend_date=ex_dividend_date,
                        record_date=record_date
                    )
                    db.add(new_dividend)
                    created_count += 1
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"第{index+2}行: {str(e)}")
                failed_count += 1
        
        # 提交所有更改
        db.commit()
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "updated_count": updated_count,
            "created_count": created_count,
            "errors": errors
        }
        
    except Exception as e:
        db.rollback()
        errors.append(f"文件处理失败: {str(e)}")
        return {
            "success_count": 0,
            "failed_count": 1,
            "updated_count": 0,
            "created_count": 0,
            "errors": errors
        }


@router.get("/", response_model=DividendListResponse, summary="获取分红列表")
async def get_dividend_list(
    fund_code: Optional[str] = Query(None, description="基金代码筛选"),
    start_date: Optional[date] = Query(None, description="开始日期筛选"),
    end_date: Optional[date] = Query(None, description="结束日期筛选"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    sort_by: Optional[str] = Query("dividend_date", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取分红列表
    
    支持按基金代码、日期范围筛选和分页
    """
    try:
        # 构建查询
        query = db.query(Dividend).join(Fund, Dividend.fund_code == Fund.fund_code)
        
        # 应用筛选条件
        if fund_code:
            query = query.filter(Dividend.fund_code.like(f"%{fund_code}%"))
        
        if start_date:
            query = query.filter(Dividend.dividend_date >= start_date)
        
        if end_date:
            query = query.filter(Dividend.dividend_date <= end_date)
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if sort_by == "dividend_date":
            if sort_order == "desc":
                query = query.order_by(desc(Dividend.dividend_date))
            else:
                query = query.order_by(Dividend.dividend_date)
        elif sort_by == "dividend_per_share":
            if sort_order == "desc":
                query = query.order_by(desc(Dividend.dividend_per_share))
            else:
                query = query.order_by(Dividend.dividend_per_share)
        else:
            query = query.order_by(desc(Dividend.dividend_date))
        
        # 应用分页
        dividends = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 构建响应数据
        dividend_responses = []
        for dividend in dividends:
            dividend_response = DividendResponse(
                id=dividend.id,
                fund_code=dividend.fund_code,
                dividend_date=dividend.dividend_date,
                dividend_per_share=dividend.dividend_per_share,
                ex_dividend_date=dividend.ex_dividend_date,
                record_date=dividend.record_date,
                fund_name=dividend.fund.fund_name if dividend.fund else None
            )
            dividend_responses.append(dividend_response)
        
        return DividendListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=dividend_responses
        )
        
    except Exception as e:
        logger.error(f"获取分红列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分红列表失败: {str(e)}"
        )


@router.get("/fund/{fund_code}/history", response_model=FundDividendHistory, summary="获取基金分红历史")
async def get_fund_dividend_history(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    获取指定基金的分红历史
    
    返回基金的分红统计和详细历史记录
    """
    try:
        # 验证基金是否存在
        fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {fund_code} 不存在"
            )
        
        # 获取分红记录
        dividends = db.query(Dividend)\
                     .filter(Dividend.fund_code == fund_code)\
                     .order_by(desc(Dividend.dividend_date))\
                     .all()
        
        if not dividends:
            return FundDividendHistory(
                fund_code=fund_code,
                fund_name=fund.fund_name,
                total_dividend_payments=0,
                total_dividend_amount=Decimal('0'),
                avg_dividend_per_payment=Decimal('0'),
                dividend_history=[]
            )
        
        # 计算统计
        total_dividend_payments = len(dividends)
        total_dividend_amount = sum(d.dividend_per_share for d in dividends)
        avg_dividend_per_payment = total_dividend_amount / total_dividend_payments
        
        # 构建分红历史
        dividend_history = []
        for dividend in dividends:
            dividend_response = DividendResponse(
                id=dividend.id,
                fund_code=dividend.fund_code,
                dividend_date=dividend.dividend_date,
                dividend_per_share=dividend.dividend_per_share,
                ex_dividend_date=dividend.ex_dividend_date,
                record_date=dividend.record_date,
                fund_name=fund.fund_name
            )
            dividend_history.append(dividend_response)
        
        return FundDividendHistory(
            fund_code=fund_code,
            fund_name=fund.fund_name,
            total_dividend_payments=total_dividend_payments,
            total_dividend_amount=total_dividend_amount,
            avg_dividend_per_payment=avg_dividend_per_payment,
            first_dividend_date=dividends[-1].dividend_date if dividends else None,
            latest_dividend_date=dividends[0].dividend_date if dividends else None,
            dividend_history=dividend_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基金分红历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基金分红历史失败: {str(e)}"
        )


@router.post("/analysis", response_model=DividendAnalysisResponse, summary="分红分析")
async def analyze_dividends(
    request: DividendAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析指定期间的分红情况
    
    可以按客户或基金进行分红收入分析
    """
    try:
        # 构建查询
        query = db.query(Dividend).join(Fund, Dividend.fund_code == Fund.fund_code)
        
        # 应用筛选条件
        query = query.filter(
            and_(
                Dividend.dividend_date >= request.start_date,
                Dividend.dividend_date <= request.end_date
            )
        )
        
        if request.fund_code:
            query = query.filter(Dividend.fund_code == request.fund_code)
        
        dividends = query.all()
        
        # 计算基本统计
        total_dividend_income = sum(d.dividend_per_share for d in dividends)
        dividend_payment_count = len(dividends)
        
        # 按基金分组统计
        fund_dividends = {}
        for dividend in dividends:
            fund_code = dividend.fund_code
            if fund_code not in fund_dividends:
                fund_dividends[fund_code] = {
                    "fund_code": fund_code,
                    "fund_name": dividend.fund.fund_name if dividend.fund else None,
                    "dividend_count": 0,
                    "total_dividend": Decimal('0'),
                    "avg_dividend": Decimal('0')
                }
            
            fund_dividends[fund_code]["dividend_count"] += 1
            fund_dividends[fund_code]["total_dividend"] += dividend.dividend_per_share
        
        # 计算平均值
        for fund_data in fund_dividends.values():
            if fund_data["dividend_count"] > 0:
                fund_data["avg_dividend"] = fund_data["total_dividend"] / fund_data["dividend_count"]
        
        # 按月度分组统计
        monthly_dividends = {}
        for dividend in dividends:
            month_key = dividend.dividend_date.strftime("%Y-%m")
            if month_key not in monthly_dividends:
                monthly_dividends[month_key] = {
                    "month": month_key,
                    "dividend_count": 0,
                    "total_dividend": Decimal('0')
                }
            
            monthly_dividends[month_key]["dividend_count"] += 1
            monthly_dividends[month_key]["total_dividend"] += dividend.dividend_per_share
        
        return DividendAnalysisResponse(
            period={
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat()
            },
            total_dividend_income=total_dividend_income,
            dividend_payment_count=dividend_payment_count,
            fund_dividends=list(fund_dividends.values()),
            monthly_dividends=list(monthly_dividends.values())
        )
        
    except Exception as e:
        logger.error(f"分红分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分红分析失败: {str(e)}"
        )