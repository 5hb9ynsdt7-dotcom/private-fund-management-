"""
净值抓取路由
NAV Crawler Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from ..database import get_db
from ..schemas.common import APIResponse
from ..services.nav_crawler_service import NavCrawlerService

logger = logging.getLogger(__name__)

# 创建净值抓取路由器
router = APIRouter(
    prefix="/api/nav-crawler",
    tags=["净值抓取"],
)


# 请求模型
class CrawlSingleRequest(BaseModel):
    fund_code: str
    access_token: Optional[str] = None
    nfp_token: Optional[str] = None


class CrawlBatchRequest(BaseModel):
    fund_codes: Optional[List[str]] = None
    access_token: Optional[str] = None
    nfp_token: Optional[str] = None


@router.post("/crawl/single", response_model=APIResponse, summary="抓取单个基金净值")
async def crawl_single_fund(
    request: CrawlSingleRequest,
    db: Session = Depends(get_db)
):
    """
    抓取单个基金的净值数据并保存到数据库

    - **fund_code**: 基金代码
    - **access_token**: 访问令牌（可选，如果已登录）
    - **nfp_token**: NFP令牌（可选，如果已登录）

    返回:
        抓取结果统计
    """
    try:
        nav_crawler_service = NavCrawlerService(db)

        # 如果提供了token，设置到爬虫
        if request.access_token and request.nfp_token:
            nav_crawler_service.set_crawler_tokens(
                request.access_token,
                request.nfp_token
            )

        result = nav_crawler_service.crawl_and_save_nav(request.fund_code)

        if result['success']:
            return APIResponse(
                success=True,
                message=f"基金 {request.fund_code} 净值抓取成功",
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', '抓取失败')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"抓取净值失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"抓取净值失败: {str(e)}"
        )


@router.post("/crawl/batch", response_model=APIResponse, summary="批量抓取基金净值")
async def crawl_batch_funds(
    request: CrawlBatchRequest,
    db: Session = Depends(get_db)
):
    """
    批量抓取多个基金的净值数据

    - **fund_codes**: 基金代码列表（可选，为空则抓取所有已配置映射的基金）
    - **access_token**: 访问令牌（可选，如果已登录）
    - **nfp_token**: NFP令牌（可选，如果已登录）

    返回:
        批量抓取结果统计
    """
    try:
        nav_crawler_service = NavCrawlerService(db)

        # 如果提供了token，设置到爬虫
        if request.access_token and request.nfp_token:
            nav_crawler_service.set_crawler_tokens(
                request.access_token,
                request.nfp_token
            )

        result = nav_crawler_service.crawl_all_funds(request.fund_codes)

        return APIResponse(
            success=True,
            message=f"批量抓取完成，共处理 {result['total_funds']} 个基金",
            data=result
        )

    except Exception as e:
        logger.error(f"批量抓取失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量抓取失败: {str(e)}"
        )


@router.post("/update-mappings", response_model=APIResponse, summary="更新产品ID映射")
async def update_product_id_mappings(
    db: Session = Depends(get_db)
):
    """
    批量更新基金表中的诺亚产品ID映射

    将配置文件中的产品代码与诺亚CRM产品ID的映射关系同步到数据库
    """
    try:
        nav_crawler_service = NavCrawlerService(db)
        result = nav_crawler_service.update_fund_noah_product_ids()

        if result['success']:
            return APIResponse(
                success=True,
                message=f"成功更新 {result['updated_count']} 个基金的产品ID映射",
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', '更新失败')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新映射失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新映射失败: {str(e)}"
        )


@router.get("/mapped-funds", response_model=APIResponse, summary="获取已配置映射的基金列表")
async def get_mapped_funds(db: Session = Depends(get_db)):
    """
    获取所有已配置诺亚CRM产品ID映射的基金列表
    按更新时间降序排列（最新配置/更新的基金排在前面）
    如果没有updated_at字段，则按基金代码降序排列
    """
    try:
        from ..models import Fund

        # 尝试按updated_at降序排列，如果字段不存在则按fund_code降序
        try:
            funds = db.query(Fund).order_by(Fund.updated_at.desc()).all()
        except Exception:
            # 如果updated_at字段不存在，回退到按fund_code降序
            funds = db.query(Fund).order_by(Fund.fund_code.desc()).all()

        fund_list = [
            {
                'fund_code': fund.fund_code,
                'fund_name': fund.fund_name,
                'noah_product_id': fund.noah_product_id,
                'has_mapping': fund.noah_product_id is not None and fund.noah_product_id != ''
            }
            for fund in funds
        ]

        mapped_count = sum(1 for f in fund_list if f['has_mapping'])

        return APIResponse(
            success=True,
            message=f"共有 {mapped_count} 个基金已配置映射",
            data={
                'funds': fund_list,
                'total_count': len(fund_list),
                'mapped_count': mapped_count
            }
        )

    except Exception as e:
        logger.error(f"获取映射基金列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取映射基金列表失败: {str(e)}"
        )


class AddMappingRequest(BaseModel):
    fund_code: str
    fund_name: Optional[str] = None
    noah_product_id: str


class AddMappingFromUrlRequest(BaseModel):
    url: str


class UpdateMappingRequest(BaseModel):
    mappings: List[dict]  # [{"fund_code": "L03100", "noah_product_id": "xxx"}]


@router.post("/add-mapping-from-url", response_model=APIResponse, summary="从产品URL添加映射")
async def add_mapping_from_url(
    request: AddMappingFromUrlRequest,
    db: Session = Depends(get_db)
):
    """
    从诺亚CRM产品详情页URL自动提取productId和productCode，并创建映射

    - **url**: 产品详情页URL，如 https://crm.noah-fund.com/#/productManagement/ProductDetailGopher?productId=xxx&productCode=L02045&...
    """
    try:
        from ..models import Fund
        from urllib.parse import urlparse, parse_qs

        # 解析URL
        url = request.url

        # 处理hash路由的URL
        if '#' in url:
            url_parts = url.split('#')
            if len(url_parts) > 1:
                hash_part = url_parts[1]
                if '?' in hash_part:
                    query_string = hash_part.split('?')[1]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="URL中未找到查询参数"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="URL格式错误"
                )
        elif '?' in url:
            query_string = url.split('?')[1]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL中未找到查询参数"
            )

        # 解析查询参数
        params = parse_qs(query_string)

        # 提取productId和productCode
        product_id = params.get('productId', [None])[0]
        product_code = params.get('productCode', [None])[0]

        if not product_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL中未找到productId参数"
            )

        if not product_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL中未找到productCode参数"
            )

        # 查找基金
        fund = db.query(Fund).filter(Fund.fund_code == product_code).first()

        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {product_code} 不存在，请先在系统中创建该基金"
            )

        # 更新映射
        old_product_id = fund.noah_product_id
        fund.noah_product_id = product_id

        # 更新updated_at时间戳以触发排序
        from datetime import datetime
        fund.updated_at = datetime.now()

        db.commit()

        action = "更新" if old_product_id else "添加"
        logger.info(f"{action}基金 {product_code} 的产品ID映射: {product_id}")

        return APIResponse(
            success=True,
            message=f"成功从URL提取并{action}基金 {product_code} 的产品ID映射",
            data={
                'fund_code': fund.fund_code,
                'fund_name': fund.fund_name,
                'noah_product_id': fund.noah_product_id,
                'action': action,
                'extracted': {
                    'product_code': product_code,
                    'product_id': product_id
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"从URL添加映射失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从URL添加映射失败: {str(e)}"
        )


@router.post("/add-mapping", response_model=APIResponse, summary="添加单个产品映射")
async def add_product_mapping(
    request: AddMappingRequest,
    db: Session = Depends(get_db)
):
    """
    为指定基金添加或更新诺亚CRM产品ID映射

    - **fund_code**: 基金代码
    - **fund_name**: 基金名称（可选）
    - **noah_product_id**: 诺亚CRM产品ID (32位UUID)
    """
    try:
        from ..models import Fund

        # 查找基金
        fund = db.query(Fund).filter(Fund.fund_code == request.fund_code).first()

        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {request.fund_code} 不存在"
            )

        # 更新映射
        old_product_id = fund.noah_product_id
        fund.noah_product_id = request.noah_product_id

        # 如果提供了基金名称，也更新基金名称
        if request.fund_name:
            fund.fund_name = request.fund_name

        # 更新updated_at时间戳以触发排序
        from datetime import datetime
        fund.updated_at = datetime.now()

        db.commit()

        action = "更新" if old_product_id else "添加"
        logger.info(f"{action}基金 {request.fund_code} 的产品ID映射: {request.noah_product_id}")

        return APIResponse(
            success=True,
            message=f"成功{action}基金 {request.fund_code} 的产品ID映射",
            data={
                'fund_code': fund.fund_code,
                'fund_name': fund.fund_name,
                'noah_product_id': fund.noah_product_id,
                'action': action
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"添加映射失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加映射失败: {str(e)}"
        )


@router.post("/batch-add-mappings", response_model=APIResponse, summary="批量添加产品映射")
async def batch_add_mappings(
    request: UpdateMappingRequest,
    db: Session = Depends(get_db)
):
    """
    批量添加或更新多个基金的诺亚CRM产品ID映射

    - **mappings**: 映射列表 [{"fund_code": "L03100", "noah_product_id": "xxx"}, ...]
    """
    try:
        from ..models import Fund

        success_count = 0
        failed_count = 0
        results = []

        for mapping in request.mappings:
            fund_code = mapping.get('fund_code')
            noah_product_id = mapping.get('noah_product_id')

            if not fund_code or not noah_product_id:
                failed_count += 1
                results.append({
                    'fund_code': fund_code,
                    'success': False,
                    'message': '缺少必要字段'
                })
                continue

            # 查找基金
            fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()

            if not fund:
                failed_count += 1
                results.append({
                    'fund_code': fund_code,
                    'success': False,
                    'message': f'基金 {fund_code} 不存在'
                })
                continue

            # 更新映射
            fund.noah_product_id = noah_product_id
            success_count += 1
            results.append({
                'fund_code': fund_code,
                'fund_name': fund.fund_name,
                'success': True,
                'message': '映射成功'
            })

        db.commit()
        logger.info(f"批量更新映射完成: 成功{success_count}，失败{failed_count}")

        return APIResponse(
            success=True,
            message=f"批量更新完成: 成功{success_count}个，失败{failed_count}个",
            data={
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results
            }
        )

    except Exception as e:
        db.rollback()
        logger.error(f"批量添加映射失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量添加映射失败: {str(e)}"
        )


@router.delete("/mapping/{fund_code}", response_model=APIResponse, summary="删除产品映射")
async def delete_product_mapping(
    fund_code: str,
    db: Session = Depends(get_db)
):
    """
    删除指定基金的诺亚CRM产品ID映射

    - **fund_code**: 基金代码
    """
    try:
        from ..models import Fund

        # 查找基金
        fund = db.query(Fund).filter(Fund.fund_code == fund_code).first()

        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"基金 {fund_code} 不存在"
            )

        # 删除映射
        fund.noah_product_id = None
        db.commit()

        logger.info(f"删除基金 {fund_code} 的产品ID映射")

        return APIResponse(
            success=True,
            message=f"成功删除基金 {fund_code} 的产品ID映射",
            data={
                'fund_code': fund_code
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除映射失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除映射失败: {str(e)}"
        )
