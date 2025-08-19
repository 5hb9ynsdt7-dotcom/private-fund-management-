"""
策略管理路由
Strategy Management Routes
按照新需求重构：实现基金策略管理API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
import pandas as pd
from io import BytesIO

from ..database import get_db
from ..schemas.strategy import (
    StrategyCreateUpdate, StrategyResponse, StrategyListResponse, 
    StrategyCreateResponse, StrategyErrorResponse, MainStrategyEnum
)
from ..models import Strategy, Fund

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/strategy",
    tags=["策略管理"],
    responses={
        404: {"model": StrategyErrorResponse, "description": "资源未找到"},
        400: {"model": StrategyErrorResponse, "description": "请求参数错误"},
        500: {"model": StrategyErrorResponse, "description": "服务器内部错误"}
    }
)


@router.post("/upload", summary="批量上传策略")
async def upload_strategies(
    files: List[UploadFile] = File(..., description="Excel策略文件列表"),
    db: Session = Depends(get_db)
):
    """
    批量上传Excel策略文件
    
    - **files**: Excel文件列表，支持.xlsx格式
    - **自动去重**: 同一基金仅保留最新记录
    - **返回**: 处理统计信息和错误详情
    
    Excel文件格式要求：
    - 产品代码/基金代码: 基金代码
    - 大类策略: 大类策略分类
    - 细分策略: 细分策略描述
    - 是否QD: true/false或1/0
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
            result = await process_strategy_excel(file_content, file.filename, db)
            
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
            
            logger.info(f"策略文件 {file.filename} 处理完成: 成功{result['success_count']}, 失败{result['failed_count']}")
        
        return {
            "success": True,
            "message": f"策略文件上传处理完成，成功{total_results['success_count']}条，失败{total_results['failed_count']}条",
            "data": total_results
        }
        
    except Exception as e:
        logger.error(f"策略文件上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件处理失败: {str(e)}"
        )


async def process_strategy_excel(file_content: bytes, filename: str, db: Session) -> dict:
    """
    处理单个策略Excel文件
    """
    success_count = 0
    failed_count = 0
    updated_count = 0
    created_count = 0
    errors = []
    
    try:
        # 读取Excel文件
        df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
        
        # 定义中英文字段映射（修复重复映射问题）
        column_mapping = {
            # 中文字段名映射 - 优先使用产品代码作为基金代码
            '产品代码': 'fund_code',
            '基金代码': 'fund_code', 
            '项目名称': 'project_name',  # 改为项目名称，避免冲突
            '产品名称': 'fund_name', 
            '大类策略': 'main_strategy',
            '细分策略': 'sub_strategy',
            '是否QD': 'is_qd',
            # 英文字段名（兼容性）
            'fund_code': 'fund_code',
            'main_strategy': 'main_strategy',
            'sub_strategy': 'sub_strategy',
            'is_qd': 'is_qd'
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
        required_columns = ['fund_code', 'main_strategy', 'sub_strategy']
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
                # 智能获取基金代码 - 优先从产品代码获取，如果没有则从项目名称获取
                fund_code = None
                if 'fund_code' in row and pd.notna(row['fund_code']):
                    fund_code = str(row['fund_code']).strip()
                elif 'project_name' in row and pd.notna(row['project_name']):
                    # 如果产品代码为空，尝试从项目名称中提取代码
                    project_name = str(row['project_name']).strip()
                    fund_code = project_name  # 暂时使用项目名称，后续可能需要进一步解析
                
                if not fund_code:
                    errors.append(f"第{index+2}行: 无法获取基金代码")
                    failed_count += 1
                    continue
                
                main_strategy = str(row['main_strategy']).strip()
                sub_strategy = str(row['sub_strategy']).strip()
                
                # 处理是否QD字段
                is_qd = False
                if 'is_qd' in row and pd.notna(row['is_qd']):
                    qd_value = str(row['is_qd']).strip().lower()
                    is_qd = qd_value in ['true', '1', 'yes', '是', 'qd']
                
                # 验证基金是否存在，如果不存在则自动创建
                fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()
                if not fund:
                    # 自动创建基金记录
                    fund_name = None
                    if 'fund_name' in row and pd.notna(row['fund_name']):
                        fund_name = str(row['fund_name']).strip()
                    else:
                        fund_name = f"基金_{fund_code}"  # 默认名称
                    
                    new_fund = Fund(
                        fund_code=fund_code,
                        fund_name=fund_name
                    )
                    db.add(new_fund)
                    db.flush()  # 立即刷新，获取新创建的基金对象
                    fund = new_fund
                    logger.info(f"自动创建基金: {fund_code} - {fund_name}")
                
                # 大类策略基本验证（允许任意值，只检查非空）
                if not main_strategy or main_strategy.lower() in ['nan', 'none', '']:
                    errors.append(f"第{index+2}行: 大类策略不能为空")
                    failed_count += 1
                    continue
                
                # 检查策略是否已存在
                existing_strategy = db.query(Strategy).filter(Strategy.fund_code == fund_code).first()
                
                if existing_strategy:
                    # 更新策略
                    existing_strategy.main_strategy = main_strategy
                    existing_strategy.sub_strategy = sub_strategy
                    existing_strategy.is_qd = is_qd
                    updated_count += 1
                else:
                    # 创建新策略
                    new_strategy = Strategy(
                        fund_code=fund_code,
                        main_strategy=main_strategy,
                        sub_strategy=sub_strategy,
                        is_qd=is_qd
                    )
                    db.add(new_strategy)
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


@router.post("/", response_model=StrategyCreateResponse, summary="创建/更新策略")
async def create_or_update_strategy(
    strategy_data: StrategyCreateUpdate,
    db: Session = Depends(get_db)
):
    """
    创建/更新策略（存在则更新）
    
    **数据模型要求：**
    - 基金代码：必填，6位字符（字母+数字）
    - 大类策略：必填，预定义值（成长/固收/宏观/其他）
    - 细分策略：必填，文本输入
    - 是否QD：布尔值，默认false
    
    **特殊处理：**
    - 基金验证：操作前检查基金是否存在
    - 策略覆盖：POST时自动更新已有策略
    
    **返回格式：**
    - 成功：{ "action": "created/updated", "fund_code": "L03126" }
    """
    try:
        # 1. 基金验证：检查基金是否存在
        fund = db.query(Fund).filter(Fund.fund_code == strategy_data.fund_code).first()
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "基金不存在",
                    "fund_code": strategy_data.fund_code,
                    "detail": "请检查基金代码是否正确"
                }
            )
        
        # 2. 检查策略是否已存在
        existing_strategy = db.query(Strategy).filter(Strategy.fund_code == strategy_data.fund_code).first()
        
        if existing_strategy:
            # 策略覆盖：更新已有策略
            existing_strategy.main_strategy = strategy_data.main_strategy
            existing_strategy.sub_strategy = strategy_data.sub_strategy
            existing_strategy.is_qd = strategy_data.is_qd
            
            db.commit()
            db.refresh(existing_strategy)
            
            logger.info(f"更新策略: {strategy_data.fund_code}")
            
            return StrategyCreateResponse(
                action="updated",
                fund_code=strategy_data.fund_code
            )
        else:
            # 创建新策略
            new_strategy = Strategy(
                fund_code=strategy_data.fund_code,
                main_strategy=strategy_data.main_strategy,
                sub_strategy=strategy_data.sub_strategy,
                is_qd=strategy_data.is_qd
            )
            
            db.add(new_strategy)
            db.commit()
            db.refresh(new_strategy)
            
            logger.info(f"创建策略: {strategy_data.fund_code}")
            
            return StrategyCreateResponse(
                action="created",
                fund_code=strategy_data.fund_code
            )
        
    except HTTPException:
        raise
    except ValueError as e:
        # 数据验证错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "数据格式错误",
                "fund_code": strategy_data.fund_code,
                "detail": str(e)
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"创建/更新策略失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "服务器内部错误",
                "fund_code": strategy_data.fund_code,
                "detail": str(e)
            }
        )


@router.get("/statistics", summary="策略统计数据")
async def get_strategy_statistics(db: Session = Depends(get_db)):
    """
    获取策略统计数据
    前端兼容接口
    """
    try:
        total_strategies = db.query(Strategy).count()
        return {
            "total_strategies": total_strategies,
            "success": True
        }
    except Exception as e:
        logger.error(f"获取策略统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略统计失败: {str(e)}"
        )


@router.get("/statistics/distribution", summary="策略分布统计")
async def get_strategy_distribution(db: Session = Depends(get_db)):
    """
    获取策略分布统计
    用于前端图表展示
    """
    try:
        # 大类策略分布
        main_strategy_stats = db.query(
            Strategy.main_strategy,
            func.count(Strategy.fund_code).label('count')
        ).group_by(Strategy.main_strategy).all()
        
        main_strategy_distribution = {
            stat.main_strategy: stat.count 
            for stat in main_strategy_stats
        }
        
        # QD产品统计
        total_strategies = db.query(Strategy).count()
        qd_count = db.query(Strategy).filter(Strategy.is_qd == True).count()
        
        return {
            "total_strategies": total_strategies,
            "main_strategy_distribution": main_strategy_distribution,
            "qd_product_count": qd_count,
            "qd_product_ratio": round(qd_count / total_strategies, 2) if total_strategies > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"获取策略统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略统计失败: {str(e)}"
        )


@router.get("/enums/main-strategies", summary="获取大类策略枚举")
async def get_main_strategy_options():
    """
    获取所有可用的大类策略选项
    用于前端下拉菜单
    """
    return {
        "main_strategies": [
            {"value": strategy.value, "label": strategy.value}
            for strategy in MainStrategyEnum
        ]
    }


@router.get("/{fund_code}", response_model=StrategyResponse, summary="获取单个基金策略")
async def get_strategy_by_fund_code(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    获取单个基金的策略配置
    
    **返回格式：**
    - 成功：完整策略JSON（含所有字段）
    - 错误：404状态码+错误详情
    """
    try:
        # 基金验证
        fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "基金不存在",
                    "fund_code": fund_code,
                    "detail": "请检查基金代码是否正确"
                }
            )
        
        # 查找策略
        strategy = db.query(Strategy).filter(Strategy.fund_code == fund_code).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "策略不存在", 
                    "fund_code": fund_code,
                    "detail": "该基金尚未配置策略"
                }
            )
        
        # 构建完整策略响应
        strategy_response = StrategyResponse(
            fund_code=strategy.fund_code,
            fund_name=fund.fund_name,
            main_strategy=strategy.main_strategy,
            sub_strategy=strategy.sub_strategy,
            is_qd=strategy.is_qd
        )
        
        return strategy_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "服务器内部错误",
                "fund_code": fund_code,
                "detail": str(e)
            }
        )


@router.delete("/{fund_code}", response_model=StrategyCreateResponse, summary="删除策略")
async def delete_strategy(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    删除指定基金的策略配置
    
    **特殊处理：**
    - 级联删除：删除策略时不影响基金数据
    - 错误处理：删除不存在策略返回404
    """
    try:
        # 查找策略
        strategy = db.query(Strategy).filter(Strategy.fund_code == fund_code).first()
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "策略不存在",
                    "fund_code": fund_code,
                    "detail": "请检查基金代码是否正确"
                }
            )
        
        # 删除策略（不影响基金数据）
        db.delete(strategy)
        db.commit()
        
        logger.info(f"删除策略成功: {fund_code}")
        
        return StrategyCreateResponse(
            action="deleted",
            fund_code=fund_code
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除策略失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "服务器内部错误",
                "fund_code": fund_code,
                "detail": str(e)
            }
        )


@router.get("/", response_model=StrategyListResponse, summary="分页策略列表")
async def get_strategy_list(
    fund_code: Optional[str] = Query(None, description="按基金代码筛选"),
    main_strategy: Optional[str] = Query(None, description="按大类策略筛选"),
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="每页记录数，默认20条"),
    # 前端兼容性参数
    size: Optional[int] = Query(None, ge=1, le=100, description="每页记录数（兼容参数）"),
    search: Optional[str] = Query(None, description="搜索基金代码（兼容参数）"),
    majorStrategy: Optional[str] = Query(None, description="大类策略（兼容参数）"),
    subStrategy: Optional[str] = Query(None, description="细分策略筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    sort_by: Optional[str] = Query("created_at", description="排序字段"),
    sort_order: Optional[str] = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取分页策略列表
    
    **分页支持：**
    - 默认每页20条，可自定义
    - 支持按基金代码/大类策略筛选
    
    **返回格式：**
    - { "total": 100, "page": 1, "page_size": 20, "data": [...] }
    """
    try:
        # 参数兼容处理
        actual_page_size = page_size or size or 20
        actual_fund_code = fund_code or search
        actual_main_strategy = main_strategy or majorStrategy
        
        # 构建查询
        query = db.query(Strategy).join(Fund)
        
        # 应用筛选条件
        if actual_fund_code:
            query = query.filter(Strategy.fund_code.like(f"%{actual_fund_code}%"))
        if actual_main_strategy:
            query = query.filter(Strategy.main_strategy == actual_main_strategy)
        if subStrategy:
            query = query.filter(Strategy.sub_strategy.like(f"%{subStrategy}%"))
        
        # 获取总数
        total = query.count()
        
        # 应用排序（简单处理，只支持默认排序）
        query = query.order_by(Strategy.fund_code)
        
        # 应用分页
        strategies = query.offset((page - 1) * actual_page_size)\
                          .limit(actual_page_size)\
                          .all()
        
        # 构建响应数据
        strategy_data = []
        for strategy in strategies:
            strategy_response = StrategyResponse(
                fund_code=strategy.fund_code,
                fund_name=strategy.fund.fund_name if strategy.fund else None,
                main_strategy=strategy.main_strategy,
                sub_strategy=strategy.sub_strategy,
                is_qd=strategy.is_qd
            )
            strategy_data.append(strategy_response)
        
        return StrategyListResponse(
            total=total,
            page=page,
            page_size=actual_page_size,
            data=strategy_data
        )
        
    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "服务器内部错误",
                "detail": str(e)
            }
        )


@router.get("/enums/main-strategies", summary="获取大类策略枚举")
async def get_main_strategy_options():
    """
    获取所有可用的大类策略选项
    用于前端下拉菜单
    """
    return {
        "main_strategies": [
            {"value": strategy.value, "label": strategy.value}
            for strategy in MainStrategyEnum
        ]
    }