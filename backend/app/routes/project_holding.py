"""
项目持仓分析模块路由
Project Holding Analysis Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import List, Optional
from datetime import date, datetime
import calendar
import logging

from ..database import get_db
from ..models import (
    ProjectHoldingAsset, 
    ProjectHoldingIndustry,
    Nav,
    Strategy,
    Fund,
    Position
)
from ..schemas.project_holding import (
    ProjectHoldingAssetCreate,
    ProjectHoldingAssetUpdate,
    ProjectHoldingAssetResponse,
    ProjectHoldingIndustryCreate,
    ProjectHoldingIndustryUpdate,
    ProjectHoldingIndustryResponse,
    ProjectListResponse,
    ProjectListItem,
    ProjectHoldingDetailResponse,
    ProjectHoldingAnalysisResponse,
    IndustryAnalysisItem,
    BulkOperationRequest,
    BulkOperationResponse
)

router = APIRouter(prefix="/api/project-holding", tags=["项目持仓分析"])

# 配置日志
logger = logging.getLogger(__name__)

# 项目同步配置 - 定义需要同步配置的项目组
PROJECT_SYNC_GROUPS = {
    "景林价值": [
        "景林价值",
        "景林价值基金专享私募证券投资子基金NY1期", 
        "景林价值封闭系列产品"
    ],
    "景林全球": [
        "景林全球三年期基金",
        "景林全球封闭系列基金"
    ],
    "高毅庆瑞6号瑞行": [
        "高毅庆瑞6号瑞行基金",
        "高毅庆瑞6号瑞行基金三年期"
    ],
    "高毅晓峰2号致信": [
        "高毅晓峰2号致信基金",
        "高毅晓峰2号致信系列私募证券投资基金"
    ],
    "高毅国鹭": [
        "高毅资产-诺亚国鹭1号基金",
        "高毅国鹭封闭式基金"
    ]
}

def get_sync_projects(project_name: str) -> List[str]:
    """获取需要同步的项目列表"""
    for group_name, projects in PROJECT_SYNC_GROUPS.items():
        if project_name in projects:
            return [p for p in projects if p != project_name]  # 排除自己
    return []

def sync_asset_records(db: Session, source_project: str, target_projects: List[str], asset_data: dict, month: date):
    """同步资产配置记录到其他项目"""
    try:
        for target_project in target_projects:
            # 检查目标项目是否存在
            project_exists = db.query(Strategy).filter(
                Strategy.project_name == target_project
            ).first()
            
            if not project_exists:
                logger.warning(f"目标项目 '{target_project}' 不存在，跳过同步")
                continue
            
            # 检查是否已存在记录
            existing_record = db.query(ProjectHoldingAsset).filter(
                and_(
                    ProjectHoldingAsset.project_name == target_project,
                    ProjectHoldingAsset.month == month
                )
            ).first()
            
            if existing_record:
                # 更新现有记录
                for key, value in asset_data.items():
                    if key != 'project_name':  # 不更新项目名称
                        setattr(existing_record, key, value)
                logger.info(f"已更新项目 '{target_project}' 的资产配置记录")
            else:
                # 创建新记录
                new_asset_data = asset_data.copy()
                new_asset_data['project_name'] = target_project
                new_record = ProjectHoldingAsset(**new_asset_data)
                db.add(new_record)
                logger.info(f"已为项目 '{target_project}' 创建资产配置记录")
                
    except Exception as e:
        logger.error(f"同步资产配置失败: {str(e)}")
        raise

def sync_industry_records(db: Session, source_project: str, target_projects: List[str], industry_data: dict, month: date):
    """同步行业配置记录到其他项目"""
    try:
        for target_project in target_projects:
            # 检查目标项目是否存在
            project_exists = db.query(Strategy).filter(
                Strategy.project_name == target_project
            ).first()
            
            if not project_exists:
                logger.warning(f"目标项目 '{target_project}' 不存在，跳过同步")
                continue
            
            # 检查是否已存在记录
            existing_record = db.query(ProjectHoldingIndustry).filter(
                and_(
                    ProjectHoldingIndustry.project_name == target_project,
                    ProjectHoldingIndustry.month == month
                )
            ).first()
            
            if existing_record:
                # 更新现有记录
                for key, value in industry_data.items():
                    if key != 'project_name':  # 不更新项目名称
                        setattr(existing_record, key, value)
                logger.info(f"已更新项目 '{target_project}' 的行业配置记录")
            else:
                # 创建新记录
                new_industry_data = industry_data.copy()
                new_industry_data['project_name'] = target_project
                new_record = ProjectHoldingIndustry(**new_industry_data)
                db.add(new_record)
                logger.info(f"已为项目 '{target_project}' 创建行业配置记录")
                
    except Exception as e:
        logger.error(f"同步行业配置失败: {str(e)}")
        raise


@router.get("/projects", response_model=ProjectListResponse)
async def get_project_list(db: Session = Depends(get_db)):
    """
    获取项目列表
    显示所有上传了净值的产品的项目名称（去重）
    """
    try:
        # 查询有净值数据的基金代码
        nav_funds = db.query(Nav.fund_code).distinct().subquery()
        
        # 获取基本项目信息
        base_query = db.query(
            Strategy.project_name,
            Strategy.main_strategy,
            Strategy.sub_strategy
        ).join(
            nav_funds, Strategy.fund_code == nav_funds.c.fund_code
        ).filter(
            Strategy.project_name.isnot(None)
        ).group_by(
            Strategy.project_name,
            Strategy.main_strategy,
            Strategy.sub_strategy
        )
        
        base_results = base_query.all()
        
        # 处理每个项目
        projects = []
        for result in base_results:
            
            # 查询最新录入数据的月份
            latest_data_month = None
            
            # 查询资产配置表的最新月份
            latest_asset_month = db.query(func.max(ProjectHoldingAsset.month)).filter(
                ProjectHoldingAsset.project_name == result.project_name
            ).scalar()
            
            # 查询行业配置表的最新月份
            latest_industry_month = db.query(func.max(ProjectHoldingIndustry.month)).filter(
                ProjectHoldingIndustry.project_name == result.project_name
            ).scalar()
            
            # 取两者中的最新月份
            if latest_asset_month and latest_industry_month:
                latest_data_month = max(latest_asset_month, latest_industry_month).strftime('%Y-%m')
            elif latest_asset_month:
                latest_data_month = latest_asset_month.strftime('%Y-%m')
            elif latest_industry_month:
                latest_data_month = latest_industry_month.strftime('%Y-%m')
            
            # 查询最新行业分类
            latest_industries = []
            if latest_industry_month:
                latest_industry_record = db.query(ProjectHoldingIndustry).filter(
                    ProjectHoldingIndustry.project_name == result.project_name,
                    ProjectHoldingIndustry.month == latest_industry_month
                ).first()
                
                if latest_industry_record:
                    # 收集所有非空的行业分类
                    for i in range(1, 6):  # industry1 到 industry5
                        industry_name = getattr(latest_industry_record, f'industry{i}')
                        if industry_name:
                            latest_industries.append(industry_name)
            
            projects.append(
                ProjectListItem(
                    project_name=result.project_name,
                    main_strategy=result.main_strategy,
                    sub_strategy=result.sub_strategy,
                    latest_data_month=latest_data_month,
                    latest_industries=latest_industries if latest_industries else None
                )
            )
        
        
        return ProjectListResponse(
            projects=projects,
            total=len(projects)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目列表失败: {str(e)}"
        )


@router.get("/{project_name}", response_model=ProjectHoldingDetailResponse)
async def get_project_holding_detail(
    project_name: str,
    db: Session = Depends(get_db)
):
    """
    获取项目持仓详情
    包括资产配置和行业配置的历史记录
    """
    try:
        # 验证项目是否存在
        project_exists = db.query(Strategy).filter(
            Strategy.project_name == project_name
        ).first()
        
        if not project_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 '{project_name}' 不存在"
            )
        
        # 查询资产配置记录
        asset_records = db.query(ProjectHoldingAsset).filter(
            ProjectHoldingAsset.project_name == project_name
        ).order_by(desc(ProjectHoldingAsset.month)).all()
        
        # 查询行业配置记录并计算实际比例
        industry_records = db.query(ProjectHoldingIndustry).filter(
            ProjectHoldingIndustry.project_name == project_name
        ).order_by(desc(ProjectHoldingIndustry.month)).all()
        
        # 为行业记录计算实际比例
        industry_responses = []
        for industry_record in industry_records:
            # 查找同月的资产配置记录获取股票总仓位
            asset_record = db.query(ProjectHoldingAsset).filter(
                and_(
                    ProjectHoldingAsset.project_name == project_name,
                    ProjectHoldingAsset.month == industry_record.month
                )
            ).first()
            
            # 计算实际比例
            actual_ratios = None
            if asset_record and asset_record.stock_total_ratio:
                actual_ratios = industry_record.calculate_actual_ratios(
                    float(asset_record.stock_total_ratio)
                )
            
            # 创建响应对象
            industry_response = ProjectHoldingIndustryResponse.from_orm(industry_record)
            industry_response.actual_ratios = actual_ratios
            industry_responses.append(industry_response)
        
        return ProjectHoldingDetailResponse(
            project_name=project_name,
            asset_records=asset_records,
            industry_records=industry_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目详情失败: {str(e)}"
        )


@router.post("/{project_name}/asset", response_model=ProjectHoldingAssetResponse)
async def create_project_asset_record(
    project_name: str,
    asset_data: ProjectHoldingAssetCreate,
    db: Session = Depends(get_db)
):
    """
    创建项目资产配置记录
    """
    try:
        # 验证项目是否存在
        project_exists = db.query(Strategy).filter(
            Strategy.project_name == project_name
        ).first()
        
        if not project_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 '{project_name}' 不存在"
            )
        
        # 检查同一项目同一月份是否已存在记录
        existing_record = db.query(ProjectHoldingAsset).filter(
            and_(
                ProjectHoldingAsset.project_name == project_name,
                ProjectHoldingAsset.month == asset_data.month
            )
        ).first()
        
        if existing_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"项目 '{project_name}' 在 {asset_data.month.strftime('%Y年%m月')} 已存在资产配置记录"
            )
        
        # 计算股票总仓位比例
        stock_total_ratio = ProjectHoldingAsset.calculate_stock_total_ratio(
            a_share=float(asset_data.a_share_ratio or 0),
            h_share=float(asset_data.h_share_ratio or 0),
            us_share=float(asset_data.us_share_ratio or 0),
            other_market=float(asset_data.other_market_ratio or 0)
        )
        
        # 创建新记录
        new_record = ProjectHoldingAsset(
            **asset_data.dict(),
            stock_total_ratio=stock_total_ratio
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        # 检查是否需要同步到其他项目
        sync_projects = get_sync_projects(project_name)
        if sync_projects:
            try:
                # 准备同步数据
                sync_data = {
                    'month': asset_data.month,
                    'a_share_ratio': asset_data.a_share_ratio,
                    'h_share_ratio': asset_data.h_share_ratio,
                    'us_share_ratio': asset_data.us_share_ratio,
                    'other_market_ratio': asset_data.other_market_ratio,
                    'global_bond_ratio': asset_data.global_bond_ratio,
                    'convertible_bond_ratio': asset_data.convertible_bond_ratio,
                    'other_ratio': asset_data.other_ratio,
                    'stock_total_ratio': new_record.stock_total_ratio
                }
                
                # 执行同步
                sync_asset_records(db, project_name, sync_projects, sync_data, asset_data.month)
                db.commit()
                logger.info(f"已将项目 '{project_name}' 的资产配置同步到 {len(sync_projects)} 个相关项目")
                
            except Exception as sync_error:
                logger.error(f"同步资产配置时出错: {str(sync_error)}")
                # 同步失败不影响主记录的创建
        
        return new_record
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建资产配置记录失败: {str(e)}"
        )


@router.post("/{project_name}/industry", response_model=ProjectHoldingIndustryResponse)
async def create_project_industry_record(
    project_name: str,
    industry_data: ProjectHoldingIndustryCreate,
    db: Session = Depends(get_db)
):
    """
    创建项目行业配置记录
    """
    try:
        # 验证项目是否存在
        project_exists = db.query(Strategy).filter(
            Strategy.project_name == project_name
        ).first()
        
        if not project_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 '{project_name}' 不存在"
            )
        
        # 检查同一项目同一月份是否已存在记录
        existing_record = db.query(ProjectHoldingIndustry).filter(
            and_(
                ProjectHoldingIndustry.project_name == project_name,
                ProjectHoldingIndustry.month == industry_data.month
            )
        ).first()
        
        if existing_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"项目 '{project_name}' 在 {industry_data.month.strftime('%Y年%m月')} 已存在行业配置记录"
            )
        
        # 创建新记录
        new_record = ProjectHoldingIndustry(**industry_data.dict())
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        # 计算实际比例（如果需要）
        response = ProjectHoldingIndustryResponse.from_orm(new_record)
        
        # 如果是基于股票仓位计算，查找同月的资产记录
        if industry_data.ratio_type == 'based_on_stock':
            asset_record = db.query(ProjectHoldingAsset).filter(
                and_(
                    ProjectHoldingAsset.project_name == project_name,
                    ProjectHoldingAsset.month == industry_data.month
                )
            ).first()
            
            if asset_record and asset_record.stock_total_ratio:
                response.actual_ratios = new_record.calculate_actual_ratios(
                    float(asset_record.stock_total_ratio)
                )
        
        # 检查是否需要同步到其他项目
        sync_projects = get_sync_projects(project_name)
        if sync_projects:
            try:
                # 准备同步数据
                sync_data = {
                    'month': industry_data.month,
                    'ratio_type': industry_data.ratio_type,
                    'industry1': industry_data.industry1,
                    'industry1_ratio': industry_data.industry1_ratio,
                    'industry2': industry_data.industry2,
                    'industry2_ratio': industry_data.industry2_ratio,
                    'industry3': industry_data.industry3,
                    'industry3_ratio': industry_data.industry3_ratio,
                    'industry4': industry_data.industry4,
                    'industry4_ratio': industry_data.industry4_ratio,
                    'industry5': industry_data.industry5,
                    'industry5_ratio': industry_data.industry5_ratio
                }
                
                # 执行同步
                sync_industry_records(db, project_name, sync_projects, sync_data, industry_data.month)
                db.commit()
                logger.info(f"已将项目 '{project_name}' 的行业配置同步到 {len(sync_projects)} 个相关项目")
                
            except Exception as sync_error:
                logger.error(f"同步行业配置时出错: {str(sync_error)}")
                # 同步失败不影响主记录的创建
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建行业配置记录失败: {str(e)}"
        )


@router.put("/asset/{record_id}", response_model=ProjectHoldingAssetResponse)
async def update_asset_record(
    record_id: int,
    asset_data: ProjectHoldingAssetUpdate,
    db: Session = Depends(get_db)
):
    """
    更新资产配置记录
    """
    try:
        record = db.query(ProjectHoldingAsset).filter(
            ProjectHoldingAsset.id == record_id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资产配置记录不存在"
            )
        
        # 更新字段
        update_data = asset_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        # 重新计算股票总仓位比例
        record.stock_total_ratio = ProjectHoldingAsset.calculate_stock_total_ratio(
            a_share=float(record.a_share_ratio or 0),
            h_share=float(record.h_share_ratio or 0),
            us_share=float(record.us_share_ratio or 0),
            other_market=float(record.other_market_ratio or 0)
        )
        
        db.commit()
        db.refresh(record)
        
        # 检查是否需要同步到其他项目
        sync_projects = get_sync_projects(record.project_name)
        if sync_projects:
            try:
                # 准备同步数据
                sync_data = {
                    'month': record.month,
                    'a_share_ratio': record.a_share_ratio,
                    'h_share_ratio': record.h_share_ratio,
                    'us_share_ratio': record.us_share_ratio,
                    'other_market_ratio': record.other_market_ratio,
                    'global_bond_ratio': record.global_bond_ratio,
                    'convertible_bond_ratio': record.convertible_bond_ratio,
                    'other_ratio': record.other_ratio,
                    'stock_total_ratio': record.stock_total_ratio
                }
                
                # 执行同步
                sync_asset_records(db, record.project_name, sync_projects, sync_data, record.month)
                db.commit()
                logger.info(f"已将项目 '{record.project_name}' 的资产配置更新同步到 {len(sync_projects)} 个相关项目")
                
            except Exception as sync_error:
                logger.error(f"同步资产配置更新时出错: {str(sync_error)}")
                # 同步失败不影响主记录的更新
        
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新资产配置记录失败: {str(e)}"
        )


@router.put("/industry/{record_id}", response_model=ProjectHoldingIndustryResponse)
async def update_industry_record(
    record_id: int,
    industry_data: ProjectHoldingIndustryUpdate,
    db: Session = Depends(get_db)
):
    """
    更新行业配置记录
    """
    try:
        record = db.query(ProjectHoldingIndustry).filter(
            ProjectHoldingIndustry.id == record_id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="行业配置记录不存在"
            )
        
        # 更新字段
        update_data = industry_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        
        db.commit()
        db.refresh(record)
        
        # 计算实际比例
        response = ProjectHoldingIndustryResponse.from_orm(record)
        
        if record.ratio_type == 'based_on_stock':
            asset_record = db.query(ProjectHoldingAsset).filter(
                and_(
                    ProjectHoldingAsset.project_name == record.project_name,
                    ProjectHoldingAsset.month == record.month
                )
            ).first()
            
            if asset_record and asset_record.stock_total_ratio:
                response.actual_ratios = record.calculate_actual_ratios(
                    float(asset_record.stock_total_ratio)
                )
        
        # 检查是否需要同步到其他项目
        sync_projects = get_sync_projects(record.project_name)
        if sync_projects:
            try:
                # 准备同步数据
                sync_data = {
                    'month': record.month,
                    'ratio_type': record.ratio_type,
                    'industry1': record.industry1,
                    'industry1_ratio': record.industry1_ratio,
                    'industry2': record.industry2,
                    'industry2_ratio': record.industry2_ratio,
                    'industry3': record.industry3,
                    'industry3_ratio': record.industry3_ratio,
                    'industry4': record.industry4,
                    'industry4_ratio': record.industry4_ratio,
                    'industry5': record.industry5,
                    'industry5_ratio': record.industry5_ratio
                }
                
                # 执行同步
                sync_industry_records(db, record.project_name, sync_projects, sync_data, record.month)
                db.commit()
                logger.info(f"已将项目 '{record.project_name}' 的行业配置更新同步到 {len(sync_projects)} 个相关项目")
                
            except Exception as sync_error:
                logger.error(f"同步行业配置更新时出错: {str(sync_error)}")
                # 同步失败不影响主记录的更新
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新行业配置记录失败: {str(e)}"
        )


@router.delete("/asset/{record_id}")
async def delete_asset_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    删除资产配置记录
    """
    try:
        record = db.query(ProjectHoldingAsset).filter(
            ProjectHoldingAsset.id == record_id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="资产配置记录不存在"
            )
        
        db.delete(record)
        db.commit()
        
        return {"message": "资产配置记录删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除资产配置记录失败: {str(e)}"
        )


@router.delete("/industry/{record_id}")
async def delete_industry_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    删除行业配置记录
    """
    try:
        record = db.query(ProjectHoldingIndustry).filter(
            ProjectHoldingIndustry.id == record_id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="行业配置记录不存在"
            )
        
        db.delete(record)
        db.commit()
        
        return {"message": "行业配置记录删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除行业配置记录失败: {str(e)}"
        )


@router.get("/{project_name}/analysis", response_model=ProjectHoldingAnalysisResponse)
async def get_project_holding_analysis(
    project_name: str,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取项目持仓分析数据
    计算行业实际占比并提供分析报告
    """
    try:
        # 验证项目是否存在
        project_exists = db.query(Strategy).filter(
            Strategy.project_name == project_name
        ).first()
        
        if not project_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 '{project_name}' 不存在"
            )
        
        # 构建查询条件
        asset_query = db.query(ProjectHoldingAsset).filter(
            ProjectHoldingAsset.project_name == project_name
        )
        industry_query = db.query(ProjectHoldingIndustry).filter(
            ProjectHoldingIndustry.project_name == project_name
        )
        
        # 添加时间范围过滤
        if start_month:
            start_date = datetime.strptime(start_month, "%Y-%m").date().replace(day=1)
            asset_query = asset_query.filter(ProjectHoldingAsset.month >= start_date)
            industry_query = industry_query.filter(ProjectHoldingIndustry.month >= start_date)
            
        if end_month:
            end_date = datetime.strptime(end_month, "%Y-%m").date().replace(day=1)
            # 计算月末日期
            _, last_day = calendar.monthrange(end_date.year, end_date.month)
            end_date = end_date.replace(day=last_day)
            asset_query = asset_query.filter(ProjectHoldingAsset.month <= end_date)
            industry_query = industry_query.filter(ProjectHoldingIndustry.month <= end_date)
        
        # 获取数据
        asset_records = asset_query.order_by(ProjectHoldingAsset.month).all()
        industry_records = industry_query.order_by(ProjectHoldingIndustry.month).all()
        
        # 生成行业分析数据
        industry_analysis = []
        for industry_record in industry_records:
            # 查找同月的资产记录
            asset_record = next(
                (ar for ar in asset_records if ar.month == industry_record.month),
                None
            )
            
            # 获取行业数据
            industries = industry_record.get_industries_with_ratios()
            
            # 计算每个行业的实际比例
            for industry_name, original_ratio in industries:
                if industry_record.ratio_type == 'based_on_stock' and asset_record:
                    actual_ratio = original_ratio * float(asset_record.stock_total_ratio or 0) / 100
                else:
                    actual_ratio = original_ratio
                
                industry_analysis.append(
                    IndustryAnalysisItem(
                        month=industry_record.month,
                        industry_name=industry_name,
                        original_ratio=original_ratio,
                        actual_ratio=actual_ratio,
                        ratio_type=industry_record.ratio_type
                    )
                )
        
        return ProjectHoldingAnalysisResponse(
            project_name=project_name,
            asset_analysis=asset_records,
            industry_analysis=industry_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目分析数据失败: {str(e)}"
        )


@router.delete("/projects/{project_name}")
async def delete_project(
    project_name: str,
    db: Session = Depends(get_db)
):
    """
    删除整个项目（包括所有相关的资产配置、行业配置记录）
    """
    try:
        # 解码项目名称
        from urllib.parse import unquote
        project_name = unquote(project_name)
        
        # 检查项目是否存在
        strategy = db.query(Strategy).filter(Strategy.project_name == project_name).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="项目未找到")
        
        # 删除所有相关的项目持仓资产记录
        asset_count = db.query(ProjectHoldingAsset).filter(
            ProjectHoldingAsset.project_name == project_name
        ).delete()
        
        # 删除所有相关的项目持仓行业记录
        industry_count = db.query(ProjectHoldingIndustry).filter(
            ProjectHoldingIndustry.project_name == project_name
        ).delete()
        
        # 删除所有相关的策略记录
        strategy_count = db.query(Strategy).filter(
            Strategy.project_name == project_name
        ).delete()
        
        db.commit()
        
        logger.info(f"项目删除成功: {project_name}, 删除策略记录: {strategy_count}, 资产记录: {asset_count}, 行业记录: {industry_count}")
        
        return {
            "message": f"项目 {project_name} 删除成功",
            "deleted_counts": {
                "strategies": strategy_count,
                "assets": asset_count,
                "industries": industry_count
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除项目失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")