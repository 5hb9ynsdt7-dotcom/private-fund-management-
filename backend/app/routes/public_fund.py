"""
公募基金API路由
Public Fund API Routes

提供公募基金管理和分析的REST API接口
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
import logging
import json

from ..database import get_db
from ..services.public_fund_service import PublicFundService
from ..schemas.public_fund import (
    # 基金主数据
    PublicFundCreate,
    PublicFundUpdate,
    PublicFundResponse,
    PublicFundListResponse,
    PublicFundFetchResponse,
    # 净值数据
    PublicFundNavCreate,
    PublicFundNavResponse,
    PublicFundNavListResponse,
    PublicFundNavUploadResponse,
    # 分析
    SingleFundAnalysisRequest,
    SingleFundAnalysisResponse,
    # 通用
    ErrorResponse,
    SuccessResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public-fund", tags=["公募基金"])


# ========== 基金主数据管理 ==========

@router.get("/funds", response_model=PublicFundListResponse, summary="获取基金列表")
async def get_fund_list(
    keyword: Optional[str] = Query(None, description="搜索关键词（基金代码或名称）"),
    fund_type: Optional[str] = Query(None, description="基金类型"),
    fund_company: Optional[str] = Query(None, description="基金公司"),
    is_active: bool = Query(True, description="是否仅查询活跃基金"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取公募基金列表（支持分页和筛选）"""
    try:
        service = PublicFundService(db)
        funds, total = service.get_fund_list(
            keyword=keyword,
            fund_type=fund_type,
            fund_company=fund_company,
            is_active=is_active,
            page=page,
            page_size=page_size
        )

        return PublicFundListResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=funds
        )

    except Exception as e:
        logger.error(f"获取基金列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/funds/{fund_code}", response_model=PublicFundResponse, summary="获取基金详情")
async def get_fund_detail(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """获取单个基金的详细信息"""
    try:
        service = PublicFundService(db)
        fund = service.get_fund_by_code(fund_code)

        if not fund:
            raise HTTPException(status_code=404, detail=f"基金代码 {fund_code} 不存在")

        return fund

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基金详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/funds", response_model=PublicFundResponse, summary="手动创建基金")
async def create_fund(
    fund_data: PublicFundCreate,
    db: Session = Depends(get_db)
):
    """手动录入基金信息"""
    try:
        service = PublicFundService(db)
        new_fund = service.create_fund(fund_data)
        return new_fund

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建基金失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/funds/fetch/{fund_code}", response_model=PublicFundFetchResponse, summary="自动抓取基金")
async def fetch_fund_auto(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """通过基金代码自动抓取并创建基金记录"""
    try:
        service = PublicFundService(db)

        # 检查是否已存在
        existing_fund = service.get_fund_by_code(fund_code)
        if existing_fund:
            return PublicFundFetchResponse(
                success=True,
                fund_code=fund_code,
                fund_name=existing_fund.fund_name,
                message="基金已存在"
            )

        # 自动抓取
        new_fund = service.fetch_fund_from_eastmoney(fund_code)

        return PublicFundFetchResponse(
            success=True,
            fund_code=fund_code,
            fund_name=new_fund.fund_name,
            message="基金信息已自动获取并保存"
        )

    except Exception as e:
        logger.error(f"自动抓取基金失败: {str(e)}")
        return PublicFundFetchResponse(
            success=False,
            fund_code=fund_code,
            message=f"抓取失败: {str(e)}"
        )


@router.put("/funds/{fund_code}", response_model=PublicFundResponse, summary="更新基金信息")
async def update_fund(
    fund_code: str,
    fund_data: PublicFundUpdate,
    db: Session = Depends(get_db)
):
    """更新基金信息"""
    try:
        service = PublicFundService(db)
        updated_fund = service.update_fund(fund_code, fund_data)
        return updated_fund

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新基金失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/funds/{fund_code}", response_model=SuccessResponse, summary="删除基金")
async def delete_fund(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """软删除基金（设置is_active=False）"""
    try:
        service = PublicFundService(db)
        service.delete_fund(fund_code)

        return SuccessResponse(
            success=True,
            message=f"基金 {fund_code} 已删除"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除基金失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 净值数据管理 ==========

@router.post("/nav/refresh/{fund_code}", response_model=PublicFundFetchResponse, summary="刷新基金净值")
async def refresh_fund_nav(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """刷新指定基金的最新净值数据"""
    try:
        service = PublicFundService(db)

        # 检查基金是否存在
        fund = service.get_fund_by_code(fund_code)
        if not fund:
            raise HTTPException(status_code=404, detail=f"基金代码 {fund_code} 不存在")

        # 刷新净值
        result = service.refresh_fund_nav(fund_code)

        return PublicFundFetchResponse(
            success=result['success'],
            fund_code=fund_code,
            fund_name=fund.fund_name,
            message=result['message']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新净值失败: {str(e)}")
        return PublicFundFetchResponse(
            success=False,
            fund_code=fund_code,
            message=f"刷新失败: {str(e)}"
        )


@router.post("/nav/refresh-all", response_model=SuccessResponse, summary="批量刷新所有基金净值")
async def refresh_all_funds_nav(
    db: Session = Depends(get_db)
):
    """批量刷新所有活跃基金的净值数据"""
    try:
        service = PublicFundService(db)

        # 获取所有活跃基金
        funds, total = service.get_fund_list(is_active=True, page=1, page_size=10000)

        if not funds:
            return SuccessResponse(
                success=True,
                message="没有需要刷新的基金"
            )

        # 批量刷新净值
        success_count = 0
        failed_count = 0
        failed_funds = []

        for fund in funds:
            try:
                result = service.refresh_fund_nav(fund.fund_code)
                if result['success']:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_funds.append({
                        'fund_code': fund.fund_code,
                        'fund_name': fund.fund_name,
                        'error': result['message']
                    })
            except Exception as e:
                failed_count += 1
                failed_funds.append({
                    'fund_code': fund.fund_code,
                    'fund_name': fund.fund_name,
                    'error': str(e)
                })

        message = f"批量刷新完成：成功 {success_count} 个，失败 {failed_count} 个"

        return SuccessResponse(
            success=True,
            message=message,
            data={
                'total': total,
                'success_count': success_count,
                'failed_count': failed_count,
                'failed_funds': failed_funds
            }
        )

    except Exception as e:
        logger.error(f"批量刷新净值失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nav/{fund_code}", response_model=PublicFundNavListResponse, summary="获取基金净值")
async def get_nav_list(
    fund_code: str,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    sort: str = Query("desc", description="排序方式：asc/desc"),
    db: Session = Depends(get_db)
):
    """获取某基金的净值时间序列"""
    try:
        service = PublicFundService(db)

        # 检查基金是否存在
        fund = service.get_fund_by_code(fund_code)
        if not fund:
            raise HTTPException(status_code=404, detail=f"基金代码 {fund_code} 不存在")

        # 获取净值数据
        nav_list = service.get_nav_list(fund_code, start_date, end_date, sort)

        return PublicFundNavListResponse(
            fund_code=fund_code,
            fund_name=fund.fund_name,
            total=len(nav_list),
            data=nav_list
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取净值列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nav", response_model=PublicFundNavResponse, summary="手动录入净值")
async def create_nav(
    nav_data: PublicFundNavCreate,
    db: Session = Depends(get_db)
):
    """手动添加单条净值记录"""
    try:
        service = PublicFundService(db)
        new_nav, is_created = service.create_or_update_nav(nav_data)

        return new_nav

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建净值记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nav/upload", response_model=PublicFundNavUploadResponse, summary="批量导入净值")
async def upload_nav(
    file: UploadFile = File(..., description="Excel文件"),
    db: Session = Depends(get_db)
):
    """上传Excel批量导入净值数据"""
    try:
        # 验证文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="仅支持Excel文件（.xlsx/.xls）")

        # 读取文件内容
        file_content = await file.read()

        # 处理上传
        service = PublicFundService(db)
        result = service.process_excel_upload(file_content, file.filename)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量导入净值失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nav/batch", response_model=SuccessResponse, summary="批量删除净值")
async def delete_nav_batch(
    nav_ids: List[int] = Query(..., description="净值记录ID列表"),
    db: Session = Depends(get_db)
):
    """批量删除净值记录"""
    try:
        service = PublicFundService(db)
        deleted_count, errors = service.delete_nav_records(nav_ids)

        message = f"成功删除 {deleted_count} 条记录"
        if errors:
            message += f"，失败 {len(errors)} 条"

        return SuccessResponse(
            success=True,
            message=message,
            data={"deleted_count": deleted_count, "errors": errors}
        )

    except Exception as e:
        logger.error(f"批量删除净值失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 投研分析 ==========

@router.post("/analysis/single", response_model=SingleFundAnalysisResponse, summary="单基金分析")
async def analyze_single_fund(
    request: SingleFundAnalysisRequest,
    db: Session = Depends(get_db)
):
    """计算单个基金的收益、回撤等指标"""
    try:
        service = PublicFundService(db)

        # 检查基金是否存在
        fund = service.get_fund_by_code(request.fund_code)
        if not fund:
            raise HTTPException(status_code=404, detail=f"基金代码 {request.fund_code} 不存在")

        # 计算指标
        indicators = service.calculate_fund_indicators(
            request.fund_code,
            request.start_date,
            request.end_date
        )

        # 计算周期信息
        days = (request.end_date - request.start_date).days
        period = {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "days": days
        }

        # 保存结果（如果需要）
        analysis_id = None
        if request.save_result:
            analysis_params = {
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat()
            }
            analysis_result = {
                "period": period,
                "indicators": indicators
            }
            analysis = service.save_analysis_result(
                analysis_type="single_fund",
                analysis_name=f"{fund.fund_name} 分析 ({request.start_date} ~ {request.end_date})",
                fund_codes=[request.fund_code],
                analysis_params=analysis_params,
                analysis_result=analysis_result
            )
            analysis_id = analysis.id

        return SingleFundAnalysisResponse(
            fund_code=request.fund_code,
            fund_name=fund.fund_name,
            period=period,
            indicators=indicators,
            analysis_id=analysis_id
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"单基金分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nav/calculate-returns/{fund_code}", response_model=SuccessResponse, summary="计算日收益率")
async def calculate_daily_returns(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """计算并更新指定基金的日收益率"""
    try:
        service = PublicFundService(db)

        # 检查基金是否存在
        fund = service.get_fund_by_code(fund_code)
        if not fund:
            raise HTTPException(status_code=404, detail=f"基金代码 {fund_code} 不存在")

        # 计算日收益率
        updated_count = service.calculate_daily_returns(fund_code)

        return SuccessResponse(
            success=True,
            message=f"成功更新 {updated_count} 条记录的日收益率"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算日收益率失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stage-performance", summary="计算阶段涨幅")
async def calculate_stage_performance(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    计算多个基金的阶段涨幅

    请求参数:
    - fund_codes: 基金代码列表
    - start_date: 起始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    - benchmark: 基准指数代码（可选，如 000300.SH）

    返回:
    - 每个基金的阶段涨幅数据
    """
    try:
        from ..models_public_fund import PublicFund, PublicFundNav
        from ..models import IndexDaily
        from sqlalchemy import and_, func

        fund_codes = request.get('fund_codes', [])
        start_date = request.get('start_date')
        end_date = request.get('end_date')
        benchmark = request.get('benchmark')

        logger.info(f"计算阶段涨幅: fund_codes={fund_codes}, start_date={start_date}, end_date={end_date}, benchmark={benchmark}")

        if not fund_codes:
            raise HTTPException(status_code=400, detail="基金代码列表不能为空")

        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="起始日期和结束日期不能为空")

        result_data = []
        errors = []

        for fund_code in fund_codes:
            try:
                # 获取公募基金信息
                fund = db.query(PublicFund).filter(PublicFund.fund_code == fund_code).first()

                if not fund:
                    error_msg = f"基金代码 {fund_code} 不存在"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

                # 获取结束日期的净值
                end_nav = db.query(PublicFundNav).filter(
                    and_(
                        PublicFundNav.fund_code == fund_code,
                        PublicFundNav.nav_date <= end_date
                    )
                ).order_by(PublicFundNav.nav_date.desc()).first()

                if not end_nav:
                    error_msg = f"基金 {fund_code} 在 {end_date} 之前没有净值数据"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

                logger.info(f"基金 {fund_code} 结束日期净值: {end_nav.nav_date} = {end_nav.accum_nav}")

                # 获取起始日期的净值
                start_nav = db.query(PublicFundNav).filter(
                    and_(
                        PublicFundNav.fund_code == fund_code,
                        PublicFundNav.nav_date <= start_date
                    )
                ).order_by(PublicFundNav.nav_date.desc()).first()

                if not start_nav:
                    error_msg = f"基金 {fund_code} 在 {start_date} 之前没有净值数据"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

                logger.info(f"基金 {fund_code} 起始日期净值: {start_nav.nav_date} = {start_nav.accum_nav}")

                # 计算阶段涨跌幅
                stage_return = ((float(end_nav.accum_nav) - float(start_nav.accum_nav)) / float(start_nav.accum_nav)) * 100

                # 获取今年1月1日的净值
                current_year = datetime.now().year
                year_start_date = f"{current_year}-01-01"

                year_start_nav = db.query(PublicFundNav).filter(
                    and_(
                        PublicFundNav.fund_code == fund_code,
                        PublicFundNav.nav_date <= year_start_date
                    )
                ).order_by(PublicFundNav.nav_date.desc()).first()

                ytd_return = None
                if year_start_nav:
                    ytd_return = ((float(end_nav.accum_nav) - float(year_start_nav.accum_nav)) / float(year_start_nav.accum_nav)) * 100
                    logger.info(f"基金 {fund_code} 今年以来涨跌幅: {ytd_return}%")

                result_data.append({
                    'fund_code': fund_code,
                    'short_name': fund.fund_name,  # 公募基金没有short_name字段
                    'nav_date': end_nav.nav_date.strftime('%Y-%m-%d'),
                    'nav': float(end_nav.accum_nav),
                    'stage_return': round(stage_return, 2),
                    'ytd_return': round(ytd_return, 2) if ytd_return is not None else None,
                    'compare_date': start_nav.nav_date.strftime('%Y-%m-%d'),
                    'compare_nav': float(start_nav.accum_nav)
                })

                logger.info(f"基金 {fund_code} 计算成功: 阶段涨幅 {stage_return:.2f}%")

            except Exception as e:
                error_msg = f"基金 {fund_code} 计算失败: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                continue

        # 如果选择了基准指数，添加基准指数数据
        if benchmark:
            try:
                # 指数代码映射
                index_names = {
                    '000300.SH': '沪深300',
                    '000905.SH': '中证500',
                    '000852.SH': '中证1000',
                    '932000.CSI': '中证2000'
                }

                # 将日期格式转换为YYYYMMDD
                start_date_str = start_date.replace('-', '')
                end_date_str = end_date.replace('-', '')
                year_start_str = f"{datetime.now().year}0101"

                # 获取结束日期的指数点位
                end_index = db.query(IndexDaily).filter(
                    and_(
                        IndexDaily.ts_code == benchmark,
                        IndexDaily.trade_date <= end_date_str
                    )
                ).order_by(IndexDaily.trade_date.desc()).first()

                if end_index:
                    # 获取起始日期的指数点位
                    start_index = db.query(IndexDaily).filter(
                        and_(
                            IndexDaily.ts_code == benchmark,
                            IndexDaily.trade_date <= start_date_str
                        )
                    ).order_by(IndexDaily.trade_date.desc()).first()

                    if start_index:
                        # 计算阶段涨跌幅
                        stage_return = ((float(end_index.close) - float(start_index.close)) / float(start_index.close)) * 100

                        # 获取今年1月1日的指数点位
                        year_start_index = db.query(IndexDaily).filter(
                            and_(
                                IndexDaily.ts_code == benchmark,
                                IndexDaily.trade_date <= year_start_str
                            )
                        ).order_by(IndexDaily.trade_date.desc()).first()

                        ytd_return = None
                        if year_start_index:
                            ytd_return = ((float(end_index.close) - float(year_start_index.close)) / float(year_start_index.close)) * 100

                        # 添加基准指数数据到结果列表
                        result_data.append({
                            'fund_code': benchmark,
                            'short_name': index_names.get(benchmark, benchmark),
                            'nav_date': end_index.trade_date[:4] + '-' + end_index.trade_date[4:6] + '-' + end_index.trade_date[6:8],
                            'nav': round(float(end_index.close), 2),
                            'stage_return': round(stage_return, 2),
                            'ytd_return': round(ytd_return, 2) if ytd_return is not None else None,
                            'compare_date': start_index.trade_date[:4] + '-' + start_index.trade_date[4:6] + '-' + start_index.trade_date[6:8],
                            'compare_nav': round(float(start_index.close), 2)
                        })

                        logger.info(f"基准指数 {benchmark} 计算成功: 阶段涨幅 {stage_return:.2f}%")
                    else:
                        logger.warning(f"基准指数 {benchmark} 在 {start_date} 之前没有数据")
                else:
                    logger.warning(f"基准指数 {benchmark} 在 {end_date} 之前没有数据")

            except Exception as e:
                logger.error(f"计算基准指数失败: {str(e)}", exc_info=True)
                errors.append(f"基准指数计算失败: {str(e)}")

        message = f'成功计算 {len(result_data)} 个基金的阶段涨幅'
        if errors:
            message += f'，{len(errors)} 个失败'
            logger.warning(f"错误详情: {errors}")

        return {
            'success': True,
            'message': message,
            'data': result_data,
            'errors': errors if errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算阶段涨幅失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
