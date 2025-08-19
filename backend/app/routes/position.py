"""
持仓分析路由
Position Analysis Routes
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
from ..schemas.position import (
    PositionResponse, PositionListResponse, PositionSearchParams,
    ClientPositionSummary, FundPositionSummary, TopHoldersResponse,
    PositionConcentrationAnalysis, ClientPortfolioSummary, ClientListResponse,
    PositionDetailResponse, EnhancedPositionResponse, StrategyDistribution
)
from ..schemas.common import APIResponse, ErrorResponse
from ..schemas.dividend import ClientDividendUploadResponse
from ..services.position_service import PositionAnalysisService
from ..models import Position, Client, Fund, Nav, DateConverter, ClientDividend, Strategy

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/position",
    tags=["持仓分析"],
    responses={
        404: {"model": ErrorResponse, "description": "资源未找到"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    }
)


@router.post("/upload", summary="批量上传持仓数据")
async def upload_positions(
    files: List[UploadFile] = File(..., description="Excel持仓文件列表"),
    override_existing: bool = Query(False, description="是否覆盖已存在数据"),
    db: Session = Depends(get_db)
):
    """
    批量上传Excel持仓文件
    
    - **files**: Excel文件列表，支持.xlsx格式
    - **override_existing**: 是否覆盖已存在的持仓数据
    - **返回**: 处理统计信息和错误详情
    
    Excel文件格式要求：
    - 集团号: 客户集团号（保留前导零）
    - 产品code: 基金代码
    - 存量时间: 日期格式(20250701或2025-07-01)
    - 含费成本: 数值
    - 不含费金额: 数值
    - 持仓份额: 数值
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
            result = await process_position_excel(file_content, file.filename, override_existing, db)
            
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
            
            logger.info(f"持仓文件 {file.filename} 处理完成: 成功{result['success_count']}, 失败{result['failed_count']}")
        
        return {
            "success": True,
            "message": f"持仓文件上传处理完成，成功{total_results['success_count']}条，失败{total_results['failed_count']}条",
            "data": total_results
        }
        
    except Exception as e:
        logger.error(f"持仓文件上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


async def process_position_excel(file_content: bytes, filename: str, override_existing: bool, db: Session) -> dict:
    """
    处理单个持仓Excel文件
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
            '集团号': 'group_id',
            '产品code': 'fund_code',
            '产品代码': 'fund_code',
            '基金代码': 'fund_code',
            '存量时间': 'stock_date',  # 存量时间作为主要日期字段
            '首次买入日期': 'first_buy_date',  # 首次买入日期单独存储
            '含费成本': 'cost_with_fee',
            '¥持仓成本(含费)(二级)': 'cost_with_fee',
            '不含费金额': 'cost_without_fee',
            '¥投资金额(不含费)(二级)': 'cost_without_fee',  # 新增映射
            '持仓份额': 'shares',
            '持仓份额(二级)': 'shares',  # 新增映射
            '客户姓名': 'client_name',
            '客户姓名(遮蔽)': 'client_name',
            '国内理财师': 'domestic_planner',
            # 英文字段名（兼容性）
            'group_id': 'group_id',
            'fund_code': 'fund_code',
            'stock_date': 'stock_date',
            'cost_with_fee': 'cost_with_fee',
            'cost_without_fee': 'cost_without_fee',
            'shares': 'shares'
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
        required_columns = ['group_id', 'fund_code', 'stock_date']
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
                group_id = DateConverter.format_group_id(str(row['group_id']).strip())
                fund_code = str(row['fund_code']).strip()
                
                # 处理日期
                stock_date_str = str(row['stock_date']).strip()
                stock_date = DateConverter.convert_date_string(stock_date_str)
                
                # 处理首次买入日期（可选字段）
                first_buy_date = None
                if 'first_buy_date' in row and pd.notna(row['first_buy_date']):
                    first_buy_date_str = str(row['first_buy_date']).strip()
                    first_buy_date = DateConverter.convert_date_string(first_buy_date_str)
                
                # 处理数值字段 - 改进解析逻辑
                def parse_numeric_field(field_name, field_value):
                    """解析数值字段，支持多种格式"""
                    if pd.isna(field_value) or field_value is None:
                        return None
                    
                    try:
                        # 转为字符串并清理
                        value_str = str(field_value).replace(',', '').replace('¥', '').replace('$', '').strip()
                        
                        # 去除括号（负数）
                        if value_str.startswith('(') and value_str.endswith(')'):
                            value_str = '-' + value_str[1:-1]
                        
                        # 空值或零值处理
                        if not value_str or value_str in ['0', '0.0', '0.00', '-', 'N/A', 'n/a', '']:
                            return None
                        
                        # 转换为Decimal
                        return Decimal(value_str)
                    except (ValueError, TypeError, Decimal.InvalidOperation) as e:
                        logger.warning(f"第{index+2}行: {field_name}格式错误: {field_value} - {str(e)}")
                        return None
                
                cost_with_fee = parse_numeric_field("含费成本", row.get('cost_with_fee'))
                cost_without_fee = parse_numeric_field("不含费金额", row.get('cost_without_fee'))
                shares = parse_numeric_field("持仓份额", row.get('shares'))
                
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
                
                # 验证客户是否存在，如果不存在则自动创建
                client = db.query(Client).filter(Client.group_id == group_id).first()
                if not client:
                    client_name = None
                    domestic_planner = None
                    
                    if 'client_name' in row and pd.notna(row['client_name']):
                        client_name = str(row['client_name']).strip()
                    
                    if 'domestic_planner' in row and pd.notna(row['domestic_planner']):
                        domestic_planner = str(row['domestic_planner']).strip()
                    
                    new_client = Client(
                        group_id=group_id,
                        obscured_name=client_name,
                        domestic_planner=domestic_planner
                    )
                    db.add(new_client)
                    db.flush()
                    client = new_client
                    logger.info(f"自动创建客户: {group_id} - {client_name}")
                
                # 检查持仓是否已存在
                existing_position = db.query(Position).filter(
                    and_(
                        Position.group_id == group_id,
                        Position.fund_code == fund_code,
                        Position.stock_date == stock_date
                    )
                ).first()
                
                if existing_position:
                    if override_existing:
                        # 更新持仓
                        existing_position.first_buy_date = first_buy_date
                        existing_position.cost_with_fee = cost_with_fee
                        existing_position.cost_without_fee = cost_without_fee
                        existing_position.shares = shares
                        updated_count += 1
                    else:
                        errors.append(f"第{index+2}行: 持仓记录已存在 ({group_id}, {fund_code}, {stock_date})")
                        failed_count += 1
                        continue
                else:
                    # 创建新持仓
                    new_position = Position(
                        group_id=group_id,
                        fund_code=fund_code,
                        stock_date=stock_date,
                        first_buy_date=first_buy_date,
                        cost_with_fee=cost_with_fee,
                        cost_without_fee=cost_without_fee,
                        shares=shares
                    )
                    db.add(new_position)
                    created_count += 1
                
                success_count += 1
                
            except Exception as e:
                error_msg = f"第{index+2}行: {str(e)}"
                errors.append(error_msg)
                logger.error(f"持仓数据处理错误: {error_msg}")
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


@router.get("/clients", response_model=ClientListResponse, summary="获取客户列表")
async def get_client_list(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    search: Optional[str] = Query(None, description="搜索客户集团号或姓名"),
    planner: Optional[str] = Query(None, description="理财师筛选"),
    sort_by: Optional[str] = Query("total_market_value", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取客户列表及其持仓汇总信息
    
    返回包含客户基本信息、总市值、收益等汇总数据的列表
    """
    try:
        # 构建客户持仓汇总查询
        query = db.query(
            Client.group_id,
            Client.obscured_name,
            Client.domestic_planner,
            func.coalesce(func.sum(Position.cost_with_fee), 0).label('total_cost'),
            func.count(func.distinct(Position.fund_code)).label('fund_count'),
            func.count(Position.id).label('position_count'),
            func.max(Position.stock_date).label('latest_update')
        ).join(Position, Client.group_id == Position.group_id)\
         .group_by(Client.group_id, Client.obscured_name, Client.domestic_planner)
        
        # 应用筛选条件
        if search:
            query = query.filter(
                or_(
                    Client.group_id.like(f"%{search}%"),
                    Client.obscured_name.like(f"%{search}%")
                )
            )
        
        if planner:
            query = query.filter(Client.domestic_planner.like(f"%{planner}%"))
        
        # 获取总数
        total = query.count()
        
        # 应用排序
        if sort_by == "total_cost":
            if sort_order == "desc":
                query = query.order_by(desc(func.coalesce(func.sum(Position.cost_with_fee), 0)))
            else:
                query = query.order_by(func.coalesce(func.sum(Position.cost_with_fee), 0))
        elif sort_by == "fund_count":
            if sort_order == "desc":
                query = query.order_by(desc(func.count(func.distinct(Position.fund_code))))
            else:
                query = query.order_by(func.count(func.distinct(Position.fund_code)))
        else:
            query = query.order_by(Client.group_id)
        
        # 应用分页
        clients = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 构建响应数据
        client_summaries = []
        for client in clients:
            # 计算市值和收益（需要获取最新净值）
            total_market_value = Decimal('0')
            total_unrealized_pnl = Decimal('0')
            
            # 获取该客户的所有持仓
            positions = db.query(Position).filter(Position.group_id == client.group_id).all()
            
            for position in positions:
                if position.shares:
                    # 获取最新净值
                    latest_nav = db.query(Nav).filter(Nav.fund_code == position.fund_code)\
                                              .order_by(desc(Nav.nav_date)).first()
                    
                    if latest_nav:
                        market_value = position.shares * latest_nav.unit_nav
                        total_market_value += market_value
                        
                        if position.cost_with_fee:
                            total_unrealized_pnl += (market_value - position.cost_with_fee)
            
            # 计算收益率
            unrealized_pnl_ratio = Decimal('0')
            if client.total_cost and client.total_cost > 0:
                unrealized_pnl_ratio = (total_unrealized_pnl / client.total_cost) * 100
            
            client_summary = ClientPortfolioSummary(
                group_id=client.group_id,
                client_name=client.obscured_name,
                domestic_planner=client.domestic_planner,
                total_cost=client.total_cost or Decimal('0'),
                total_market_value=total_market_value,
                total_unrealized_pnl=total_unrealized_pnl,
                unrealized_pnl_ratio=unrealized_pnl_ratio,
                position_count=client.position_count or 0,
                fund_count=client.fund_count or 0,
                latest_update=client.latest_update
            )
            client_summaries.append(client_summary)
        
        return ClientListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=client_summaries
        )
        
    except Exception as e:
        logger.error(f"获取客户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取客户列表失败: {str(e)}"
        )


@router.get("/clients/{group_id}", response_model=PositionDetailResponse, summary="获取客户持仓详情")
async def get_client_position_detail(
    group_id: str,
    as_of_date: Optional[date] = Query(None, description="截止日期"),
    start_date: Optional[date] = Query(None, description="阶段收益开始日期"),
    end_date: Optional[date] = Query(None, description="阶段收益结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取客户持仓详情
    
    返回客户的详细持仓信息、收益分析和策略分布
    """
    try:
        # 验证客户是否存在
        client = db.query(Client).filter(Client.group_id == group_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"客户 {group_id} 不存在"
            )
        
        # 获取持仓列表(联合查询策略信息)
        positions_query = db.query(Position, Fund, Strategy)\
                           .join(Fund, Position.fund_code == Fund.fund_code)\
                           .outerjoin(Strategy, Fund.fund_code == Strategy.fund_code)\
                           .filter(Position.group_id == group_id)
        
        if as_of_date:
            positions_query = positions_query.filter(Position.stock_date <= as_of_date)
        
        position_data = positions_query.all()
        
        # 构建增强持仓响应数据
        enhanced_positions = []
        total_cost = Decimal('0')
        total_market_value = Decimal('0')
        total_unrealized_pnl = Decimal('0')
        total_dividends = Decimal('0')
        
        # 策略分布统计
        holding_stats = {}  # fund_code -> market_value
        major_strategy_stats = {}  # major_strategy -> market_value
        sub_strategy_stats = {}  # sub_strategy -> market_value
        
        for position, fund, strategy in position_data:
            # 获取最新净值
            nav_query = db.query(Nav).filter(Nav.fund_code == position.fund_code)
            if as_of_date:
                nav_query = nav_query.filter(Nav.nav_date <= as_of_date)
            
            latest_nav = nav_query.order_by(desc(Nav.nav_date)).first()
            
            # 获取客户分红记录
            dividend_amount = db.query(func.sum(ClientDividend.confirmed_amount))\
                               .filter(and_(
                                   ClientDividend.group_id == group_id,
                                   ClientDividend.fund_code == position.fund_code,
                                   ClientDividend.transaction_type == '现金红利'
                               )).scalar() or Decimal('0')
            
            # 计算买入净值
            buy_nav = None
            if position.cost_without_fee and position.shares and position.shares > 0:
                buy_nav = position.cost_without_fee / position.shares
            
            # 计算收益数据
            current_nav = latest_nav.unit_nav if latest_nav else None
            latest_nav_date = latest_nav.nav_date if latest_nav else None
            current_market_value = None
            holding_return = None
            holding_return_rate = None
            
            if position.shares and current_nav:
                current_market_value = position.shares * current_nav
                total_market_value += current_market_value
                
                # 持有收益 = 最新净值*持仓份额 - 持仓成本(含费) - 现金分红累计金额
                if position.cost_with_fee:
                    holding_return = current_market_value - position.cost_with_fee - dividend_amount
                    total_unrealized_pnl += holding_return
                    holding_return_rate = (holding_return / position.cost_with_fee) * 100
            
            if position.cost_with_fee:
                total_cost += position.cost_with_fee
            
            total_dividends += dividend_amount
            
            # 计算阶段收益
            period_return = None
            if start_date and end_date and position.shares:
                # 确定期初净值：如果买入时间在阶段内，使用买入净值；否则使用开始日净值
                first_buy_date = position.first_buy_date or position.stock_date
                
                if first_buy_date and first_buy_date > start_date:
                    # 买入时间在阶段中间，使用买入净值作为期初净值
                    period_start_nav = buy_nav if buy_nav else None
                else:
                    # 买入时间在阶段开始前，获取开始日净值
                    start_nav_query = db.query(Nav).filter(
                        and_(Nav.fund_code == position.fund_code, Nav.nav_date >= start_date)
                    ).order_by(Nav.nav_date)
                    start_nav = start_nav_query.first()
                    period_start_nav = start_nav.unit_nav if start_nav else None
                
                # 获取结束日净值：取≤结束日期的最近净值
                end_nav_query = db.query(Nav).filter(
                    and_(Nav.fund_code == position.fund_code, Nav.nav_date <= end_date)
                ).order_by(desc(Nav.nav_date))
                end_nav = end_nav_query.first()
                period_end_nav = end_nav.unit_nav if end_nav else None
                
                if period_start_nav and period_end_nav:
                    # 阶段收益 = (结束日净值 - 期初净值) × 持仓份额
                    period_return = (period_end_nav - period_start_nav) * position.shares
            
            # 策略信息
            major_strategy = strategy.main_strategy if strategy else "未分类"
            sub_strategy = strategy.sub_strategy if strategy else "未知策略"
            is_qd = strategy.is_qd if strategy else False
            
            # 统计策略分布
            if current_market_value:
                # 持仓分布（按基金）
                fund_display_name = fund.fund_name or position.fund_code
                holding_stats[fund_display_name] = holding_stats.get(fund_display_name, 0) + float(current_market_value)
                
                # 大类策略分布
                major_strategy_stats[major_strategy] = major_strategy_stats.get(major_strategy, 0) + float(current_market_value)
                
                # 细分策略分布
                sub_strategy_stats[sub_strategy] = sub_strategy_stats.get(sub_strategy, 0) + float(current_market_value)
            
            enhanced_position = EnhancedPositionResponse(
                id=position.id,
                group_id=position.group_id,
                fund_code=position.fund_code,
                fund_name=fund.fund_name if fund else None,
                first_buy_date=position.first_buy_date,  # 首次买入日期
                cost_with_fee=position.cost_with_fee,  # 持仓成本(含费)
                cost_without_fee=position.cost_without_fee,  # 投资金额(不含费)
                shares=position.shares,  # 持仓份额
                buy_nav=buy_nav,  # 买入净值
                latest_nav=current_nav,
                latest_nav_date=latest_nav_date,
                current_market_value=current_market_value,
                total_dividends=dividend_amount,
                holding_return=holding_return,
                holding_return_rate=holding_return_rate,
                period_return=period_return,  # 阶段收益
                major_strategy=major_strategy,
                sub_strategy=sub_strategy,
                is_qd=is_qd  # QD产品标识
            )
            enhanced_positions.append(enhanced_position)
        
        # 计算客户汇总
        unrealized_pnl_ratio = Decimal('0')
        if total_cost > 0:
            unrealized_pnl_ratio = (total_unrealized_pnl / total_cost) * 100
        
        client_summary = ClientPortfolioSummary(
            group_id=client.group_id,
            client_name=client.obscured_name,
            domestic_planner=client.domestic_planner,
            total_cost=total_cost,
            total_market_value=total_market_value,
            total_unrealized_pnl=total_unrealized_pnl,
            unrealized_pnl_ratio=unrealized_pnl_ratio,
            position_count=len(enhanced_positions),
            fund_count=len(set(p.fund_code for p in enhanced_positions)),
            latest_update=max((position.stock_date for position, fund, strategy in position_data), default=None)
        )
        
        # 构建策略分布数据
        def build_distribution_list(stats_dict, total_value):
            distributions = []
            for name, value in stats_dict.items():
                percentage = (value / total_value * 100) if total_value > 0 else 0
                distributions.append(StrategyDistribution(
                    strategy_name=name,
                    position_count=1,  # 简化处理
                    total_market_value=Decimal(str(value)),
                    percentage=percentage
                ))
            return sorted(distributions, key=lambda x: x.total_market_value, reverse=True)
        
        total_mv = float(total_market_value)
        
        # 计算今年以来收益
        ytd_return = Decimal('0')  # 初始化
        current_year = date.today().year
        
        for position, fund, strategy in position_data:
            if not position.shares:
                continue
                
            position_ytd_return = Decimal('0')
            
            # 获取今年初始净值（期初净值）- 与阶段收益计算逻辑保持一致
            # 如果首次买入日期在今年内，则使用买入净值作为期初净值
            # 如果首次买入日期在今年之前，则使用今年1月1日的净值作为期初净值
            year_start = date(current_year, 1, 1)
            first_buy_date = position.first_buy_date or position.stock_date
            
            if first_buy_date and first_buy_date >= year_start:
                # 首次买入日期在今年内，使用买入净值作为期初净值
                if position.cost_without_fee and position.shares > 0:
                    initial_nav = position.cost_without_fee / position.shares
                else:
                    continue  # 无法计算买入净值，跳过
            else:
                # 首次买入日期在今年之前，使用今年1月1日净值作为期初净值
                year_start_nav = db.query(Nav).filter(
                    and_(Nav.fund_code == position.fund_code, Nav.nav_date >= year_start)
                ).order_by(Nav.nav_date).first()
                
                if not year_start_nav:
                    continue  # 没有今年的净值数据，跳过
                initial_nav = year_start_nav.unit_nav
            
            # 获取最新净值
            latest_nav_record = db.query(Nav).filter(Nav.fund_code == position.fund_code)\
                                             .order_by(desc(Nav.nav_date)).first()
            
            if not latest_nav_record:
                continue  # 没有净值数据，跳过
            
            current_nav_value = latest_nav_record.unit_nav
            
            # 计算净值收益 = (最新净值 - 期初净值) × 持仓份额
            nav_return = (current_nav_value - initial_nav) * position.shares
            
            # 获取今年的现金分红
            cash_dividends = db.query(func.sum(ClientDividend.confirmed_amount))\
                              .filter(and_(
                                  ClientDividend.group_id == group_id,
                                  ClientDividend.fund_code == position.fund_code,
                                  ClientDividend.transaction_type == '现金红利',
                                  ClientDividend.confirmed_date >= year_start
                              )).scalar() or Decimal('0')
            
            # 今年以来收益 = 净值收益 + 现金分红
            position_ytd_return = nav_return + cash_dividends
            ytd_return += position_ytd_return
        
        # 收益概览数据
        revenue_overview = {
            "total_investment": float(total_cost),
            "total_market_value": float(total_market_value),
            "total_pnl": float(total_unrealized_pnl),
            "total_dividends": float(total_dividends),
            "ytd_return": float(ytd_return),  # 今年以来收益
            "pnl_ratio": float(unrealized_pnl_ratio)
        }
        
        # 按策略分组持仓（用于表格显示）
        strategy_groups = {}
        for pos in enhanced_positions:
            major_strategy = pos.major_strategy or "未分类"
            if major_strategy not in strategy_groups:
                strategy_groups[major_strategy] = []
            strategy_groups[major_strategy].append(pos)
        
        # 排序策略组内的持仓
        def sort_positions_within_group(positions, group_name):
            if group_name == "成长配置":
                # 成长策略组：主观多头→股票多头→股票多空→量化多头
                strategy_order = ["主观多头", "股票多头", "股票多空", "量化多头"]
                positions.sort(key=lambda p: (
                    strategy_order.index(p.sub_strategy) if p.sub_strategy in strategy_order else 999,
                    p.first_buy_date
                ))
            else:
                # 其他策略组：按策略名称排序，同策略内按买入日期排序
                positions.sort(key=lambda p: (p.sub_strategy or "", p.first_buy_date))
        
        for group_name, positions in strategy_groups.items():
            sort_positions_within_group(positions, group_name)
        
        return PositionDetailResponse(
            client_info=client_summary,
            positions=enhanced_positions,
            revenue_overview=revenue_overview,
            holding_distribution=build_distribution_list(holding_stats, total_mv),
            major_strategy_distribution=build_distribution_list(major_strategy_stats, total_mv),
            sub_strategy_distribution=build_distribution_list(sub_strategy_stats, total_mv),
            grouped_positions=strategy_groups
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取客户持仓详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取客户持仓详情失败: {str(e)}"
        )


@router.delete("/clients/{group_id}", summary="删除客户及其所有持仓")
async def delete_client(
    group_id: str,
    db: Session = Depends(get_db)
):
    """
    删除客户及其所有持仓数据
    
    这将删除客户记录和所有相关的持仓数据
    """
    try:
        # 验证客户是否存在
        client = db.query(Client).filter(Client.group_id == group_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"客户 {group_id} 不存在"
            )
        
        # 获取持仓数量用于返回信息
        position_count = db.query(Position).filter(Position.group_id == group_id).count()
        
        # 删除客户（由于外键级联删除，持仓数据也会被删除）
        db.delete(client)
        db.commit()
        
        logger.info(f"删除客户成功: {group_id}, 同时删除了 {position_count} 条持仓记录")
        
        return {
            "success": True,
            "message": f"成功删除客户 {group_id} 及其 {position_count} 条持仓记录",
            "data": {
                "group_id": group_id,
                "deleted_positions": position_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除客户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除客户失败: {str(e)}"
        )


@router.get("/list", response_model=PositionListResponse, summary="获取持仓列表")
async def get_position_list(
    group_id: Optional[str] = Query(None, description="客户集团号筛选"),
    fund_code: Optional[str] = Query(None, description="基金代码筛选"),
    start_date: Optional[date] = Query(None, description="开始日期筛选"),
    end_date: Optional[date] = Query(None, description="结束日期筛选"),
    domestic_planner: Optional[str] = Query(None, description="理财师筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=1000, description="每页记录数"),
    db: Session = Depends(get_db)
):
    """
    获取持仓记录列表（支持分页和多条件筛选）
    
    - **group_id**: 可选，按客户集团号筛选
    - **fund_code**: 可选，按基金代码筛选
    - **start_date**: 可选，按存量时间筛选（开始日期）
    - **end_date**: 可选，按存量时间筛选（结束日期）
    - **domestic_planner**: 可选，按理财师筛选
    - **page**: 页码，从1开始
    - **page_size**: 每页记录数
    """
    try:
        position_service = PositionAnalysisService(db)
        positions, total = position_service.get_position_list(
            group_id=group_id,
            fund_code=fund_code,
            start_date=start_date,
            end_date=end_date,
            domestic_planner=domestic_planner,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应模型
        position_responses = []
        for pos in positions:
            pos_response = PositionResponse.from_orm(pos)
            pos_response.client_name = pos.client.obscured_name if pos.client else None
            pos_response.fund_name = pos.fund.fund_name if pos.fund else None
            pos_response.domestic_planner = pos.client.domestic_planner if pos.client else None
            position_responses.append(pos_response)
        
        return PositionListResponse(
            positions=position_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取持仓列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取持仓列表失败: {str(e)}"
        )


@router.get("/client/{group_id}", response_model=APIResponse, summary="客户持仓分析")
async def analyze_client_positions(
    group_id: str,
    db: Session = Depends(get_db)
):
    """
    分析指定客户的全部持仓情况
    
    - **group_id**: 客户集团号
    - **返回**: 客户持仓汇总分析，包括收益率、市值等
    """
    try:
        position_service = PositionAnalysisService(db)
        client_summary = position_service.analyze_client_positions(group_id)
        
        return APIResponse(
            success=True,
            message=f"客户 {group_id} 持仓分析完成",
            data=client_summary
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"客户持仓分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"客户持仓分析失败: {str(e)}"
        )


@router.get("/fund/{fund_code}", response_model=APIResponse, summary="基金持仓分析")
async def analyze_fund_positions(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    分析指定基金的所有持仓情况
    
    - **fund_code**: 基金代码
    - **返回**: 基金持仓汇总分析，包括客户分布、总市值等
    """
    try:
        position_service = PositionAnalysisService(db)
        fund_summary = position_service.analyze_fund_positions(fund_code)
        
        return APIResponse(
            success=True,
            message=f"基金 {fund_code} 持仓分析完成",
            data=fund_summary
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"基金持仓分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"基金持仓分析失败: {str(e)}"
        )


@router.get("/fund/{fund_code}/top-holders", response_model=TopHoldersResponse, summary="基金前十大持有人")
async def get_fund_top_holders(
    fund_code: str,
    top_n: int = Query(10, ge=1, le=50, description="返回前N名，默认10"),
    db: Session = Depends(get_db)
):
    """
    获取基金前N大持有人列表
    
    - **fund_code**: 基金代码
    - **top_n**: 返回前N名持有人，默认10名
    - **返回**: 持有人排名、份额、市值、占比等信息
    """
    try:
        position_service = PositionAnalysisService(db)
        top_holders = position_service.get_fund_top_holders(fund_code, top_n)
        
        return top_holders
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取基金前十大持有人失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基金前十大持有人失败: {str(e)}"
        )


@router.get("/fund/{fund_code}/concentration", response_model=PositionConcentrationAnalysis, summary="持仓集中度分析")
async def analyze_position_concentration(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    分析基金持仓集中度
    
    - **fund_code**: 基金代码
    - **返回**: 赫芬达尔指数、前N名集中度、持有人分布等指标
    """
    try:
        position_service = PositionAnalysisService(db)
        concentration_analysis = position_service.analyze_position_concentration(fund_code)
        
        return concentration_analysis
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"持仓集中度分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"持仓集中度分析失败: {str(e)}"
        )


@router.get("/summary/by-planner", response_model=APIResponse, summary="按理财师汇总持仓")
async def get_positions_by_planner(
    domestic_planner: Optional[str] = Query(None, description="理财师名称筛选"),
    db: Session = Depends(get_db)
):
    """
    按理财师汇总客户持仓情况
    
    - **domestic_planner**: 可选，指定理财师筛选
    - **返回**: 理财师管理的客户及其持仓汇总
    """
    try:
        # 构建查询
        query = db.query(Client)
        if domestic_planner:
            query = query.filter(Client.domestic_planner.like(f"%{domestic_planner}%"))
        
        clients = query.all()
        
        planner_summary = {}
        for client in clients:
            planner = client.domestic_planner or "未分配"
            
            if planner not in planner_summary:
                planner_summary[planner] = {
                    "planner_name": planner,
                    "client_count": 0,
                    "total_cost": 0,
                    "clients": []
                }
            
            # 获取客户持仓统计
            positions = db.query(Position).filter(Position.group_id == client.group_id).all()
            
            if positions:
                client_total_cost = sum([float(pos.cost_with_fee or 0) for pos in positions])
                fund_count = len(set([pos.fund_code for pos in positions]))
                
                planner_summary[planner]["client_count"] += 1
                planner_summary[planner]["total_cost"] += client_total_cost
                planner_summary[planner]["clients"].append({
                    "group_id": client.group_id,
                    "client_name": client.obscured_name,
                    "fund_count": fund_count,
                    "total_cost": client_total_cost
                })
        
        return APIResponse(
            success=True,
            message="理财师持仓汇总完成",
            data={
                "planner_summary": list(planner_summary.values()),
                "total_planners": len(planner_summary)
            }
        )
        
    except Exception as e:
        logger.error(f"理财师持仓汇总失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"理财师持仓汇总失败: {str(e)}"
        )


@router.get("/statistics/overview", response_model=APIResponse, summary="持仓统计概览")
async def get_position_statistics(db: Session = Depends(get_db)):
    """
    获取持仓统计概览
    
    - **返回**: 总体持仓统计、基金分布、客户分布等信息
    """
    try:
        from sqlalchemy import func, distinct
        
        # 基础统计
        total_positions = db.query(Position).count()
        total_clients = db.query(distinct(Position.group_id)).count()
        total_funds = db.query(distinct(Position.fund_code)).count()
        
        # 资金统计
        total_cost_stats = db.query(
            func.sum(Position.cost_with_fee).label('total_cost_with_fee'),
            func.sum(Position.cost_without_fee).label('total_cost_without_fee'),
            func.sum(Position.shares).label('total_shares')
        ).first()
        
        # 按基金统计
        fund_stats = db.query(
            Position.fund_code,
            Fund.fund_name,
            func.count(distinct(Position.group_id)).label('client_count'),
            func.sum(Position.cost_with_fee).label('total_cost'),
            func.sum(Position.shares).label('total_shares')
        ).join(Fund).group_by(Position.fund_code, Fund.fund_name)\
         .order_by(func.sum(Position.cost_with_fee).desc()).limit(10).all()
        
        # 按客户统计
        client_stats = db.query(
            Position.group_id,
            Client.obscured_name,
            Client.domestic_planner,
            func.count(distinct(Position.fund_code)).label('fund_count'),
            func.sum(Position.cost_with_fee).label('total_cost')
        ).join(Client).group_by(
            Position.group_id, Client.obscured_name, Client.domestic_planner
        ).order_by(func.sum(Position.cost_with_fee).desc()).limit(10).all()
        
        return APIResponse(
            success=True,
            message="持仓统计概览获取成功",
            data={
                "overview": {
                    "total_positions": total_positions,
                    "total_clients": total_clients,
                    "total_funds": total_funds,
                    "total_cost_with_fee": float(total_cost_stats.total_cost_with_fee or 0),
                    "total_cost_without_fee": float(total_cost_stats.total_cost_without_fee or 0),
                    "total_shares": float(total_cost_stats.total_shares or 0)
                },
                "top_funds": [
                    {
                        "fund_code": stat.fund_code,
                        "fund_name": stat.fund_name,
                        "client_count": stat.client_count,
                        "total_cost": float(stat.total_cost or 0),
                        "total_shares": float(stat.total_shares or 0)
                    } for stat in fund_stats
                ],
                "top_clients": [
                    {
                        "group_id": stat.group_id,
                        "client_name": stat.obscured_name,
                        "domestic_planner": stat.domestic_planner,
                        "fund_count": stat.fund_count,
                        "total_cost": float(stat.total_cost or 0)
                    } for stat in client_stats
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"获取持仓统计概览失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取持仓统计概览失败: {str(e)}"
        )


@router.post("/client-dividends/upload", response_model=ClientDividendUploadResponse, summary="批量上传客户分红数据")
async def upload_client_dividends(
    files: List[UploadFile] = File(..., description="Excel分红文件列表"),
    override_existing: bool = Query(False, description="是否覆盖已存在数据"),
    db: Session = Depends(get_db)
):
    """
    批量上传客户分红Excel文件
    
    Excel文件格式要求：
    - 集团号: 客户集团号
    - 产品代码/基金代码: 基金代码
    - 产品名称: 基金名称(可选，用于映射)
    - 交易类型: 现金红利/红利转投
    - 确认金额(原币): 分红金额
    - 确认份额: 红利转投份额(红利转投时必填)
    - 确认日期: 分红确认日期
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
        "errors": []
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
            result = await process_client_dividend_excel(file_content, file.filename, override_existing, db)
            
            # 累计统计
            total_results["success_count"] += result["success_count"]
            total_results["failed_count"] += result["failed_count"]
            total_results["updated_count"] += result["updated_count"]
            total_results["created_count"] += result["created_count"]
            total_results["errors"].extend([f"{file.filename}: {error}" for error in result["errors"]])
            
            logger.info(f"客户分红文件 {file.filename} 处理完成: 成功{result['success_count']}, 失败{result['failed_count']}")
        
        return ClientDividendUploadResponse(
            success_count=total_results["success_count"],
            failed_count=total_results["failed_count"],
            updated_count=total_results["updated_count"],
            created_count=total_results["created_count"],
            errors=total_results["errors"]
        )
        
    except Exception as e:
        logger.error(f"客户分红文件上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


async def process_client_dividend_excel(file_content: bytes, filename: str, override_existing: bool, db: Session) -> dict:
    """
    处理单个客户分红Excel文件
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
            '集团号': 'group_id',
            '产品代码': 'fund_code',
            '基金代码': 'fund_code',
            '产品名称': 'fund_name',
            '基金名称': 'fund_name',
            '交易类型': 'transaction_type',
            '确认金额(原币)': 'confirmed_amount',
            '确认金额': 'confirmed_amount',
            '确认份额': 'confirmed_shares',
            '确认日期': 'confirmed_date',
            # 英文字段名（兼容性）
            'group_id': 'group_id',
            'fund_code': 'fund_code',
            'fund_name': 'fund_name',
            'transaction_type': 'transaction_type',
            'confirmed_amount': 'confirmed_amount',
            'confirmed_shares': 'confirmed_shares',
            'confirmed_date': 'confirmed_date'
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
        required_columns = ['group_id', 'fund_code', 'transaction_type', 'confirmed_date']
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
                group_id = DateConverter.format_group_id(str(row['group_id']).strip())
                fund_code = str(row['fund_code']).strip()
                transaction_type = str(row['transaction_type']).strip()
                
                # 处理日期
                confirmed_date_str = str(row['confirmed_date']).strip()
                confirmed_date = DateConverter.convert_date_string(confirmed_date_str)
                
                # 处理数值字段
                def parse_numeric_field(field_name, field_value):
                    """解析数值字段，支持多种格式"""
                    if pd.isna(field_value) or field_value is None:
                        return None
                    
                    try:
                        # 转为字符串并清理
                        value_str = str(field_value).replace(',', '').replace('¥', '').replace('$', '').strip()
                        
                        # 去除括号（负数）
                        if value_str.startswith('(') and value_str.endswith(')'):
                            value_str = '-' + value_str[1:-1]
                        
                        # 空值或零值处理
                        if not value_str or value_str in ['0', '0.0', '0.00', '-', 'N/A', 'n/a', '']:
                            return None
                        
                        # 转换为Decimal
                        return Decimal(value_str)
                    except (ValueError, TypeError, Decimal.InvalidOperation) as e:
                        logger.warning(f"第{index+2}行: {field_name}格式错误: {field_value} - {str(e)}")
                        return None
                
                confirmed_amount = parse_numeric_field("确认金额", row.get('confirmed_amount'))
                confirmed_shares = parse_numeric_field("确认份额", row.get('confirmed_shares'))
                
                # 验证基金是否存在，如果不存在则自动创建
                fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()
                if not fund:
                    fund_name = row.get('fund_name', f"基金_{fund_code}")  # 使用Excel中的基金名称或默认名称
                    new_fund = Fund(
                        fund_code=fund_code,
                        fund_name=fund_name
                    )
                    db.add(new_fund)
                    db.flush()
                    fund = new_fund
                    logger.info(f"自动创建基金: {fund_code} - {fund_name}")
                
                # 验证客户是否存在
                client = db.query(Client).filter(Client.group_id == group_id).first()
                if not client:
                    errors.append(f"第{index+2}行: 客户 {group_id} 不存在，请先上传客户持仓数据")
                    failed_count += 1
                    continue
                
                # 检查分红记录是否已存在
                existing_dividend = db.query(ClientDividend).filter(
                    and_(
                        ClientDividend.group_id == group_id,
                        ClientDividend.fund_code == fund_code,
                        ClientDividend.confirmed_date == confirmed_date,
                        ClientDividend.transaction_type == transaction_type
                    )
                ).first()
                
                if existing_dividend:
                    if override_existing:
                        # 更新分红记录
                        existing_dividend.confirmed_amount = confirmed_amount
                        existing_dividend.confirmed_shares = confirmed_shares
                        updated_count += 1
                    else:
                        errors.append(f"第{index+2}行: 分红记录已存在 ({group_id}, {fund_code}, {confirmed_date}, {transaction_type})")
                        failed_count += 1
                        continue
                else:
                    # 创建新分红记录
                    new_dividend = ClientDividend(
                        group_id=group_id,
                        fund_code=fund_code,
                        transaction_type=transaction_type,
                        confirmed_amount=confirmed_amount,
                        confirmed_shares=confirmed_shares,
                        confirmed_date=confirmed_date
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