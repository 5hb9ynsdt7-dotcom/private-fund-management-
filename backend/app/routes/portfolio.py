"""
公募基金实盘组合路由
Public Fund Portfolio Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal
import logging

from ..database import get_db
from ..services.portfolio_service import PortfolioService
from ..models_public_fund import PublicFund
from ..models import Fund  # 添加私募基金模型
from ..schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PortfolioDetailResponse,
    TransactionCreate,
    TransactionResponse,
    PositionResponse,
    PortfolioNavResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/portfolio",
    tags=["实盘组合"]
)


# ========== 组合管理 ==========

@router.post("", response_model=PortfolioResponse, summary="创建组合")
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """
    创建新的实盘组合
    """
    try:
        service = PortfolioService(db)
        new_portfolio = service.create_portfolio(portfolio)

        return PortfolioResponse(
            id=new_portfolio.id,
            portfolio_name=new_portfolio.portfolio_name,
            description=new_portfolio.description,
            cash_balance=new_portfolio.cash_balance,
            is_active=new_portfolio.is_active,
            portfolio_type=new_portfolio.portfolio_type,
            update_frequency=new_portfolio.update_frequency,
            created_at=new_portfolio.created_at,
            updated_at=new_portfolio.updated_at,
            total_invested=Decimal('0'),
            position_count=0,
            current_value=Decimal('0'),
            total_return=Decimal('0'),
            total_return_rate=Decimal('0')
        )

    except Exception as e:
        logger.error(f"创建组合失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建组合失败: {str(e)}"
        )


@router.get("", response_model=PortfolioListResponse, summary="获取组合列表")
async def get_portfolio_list(
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: Session = Depends(get_db)
):
    """
    获取所有实盘组合列表
    """
    try:
        service = PortfolioService(db)
        portfolios = service.get_portfolio_list(is_active)

        # 为每个组合计算当前市值和收益
        portfolio_responses = []
        for portfolio in portfolios:
            try:
                value_data = service.calculate_portfolio_value(portfolio.id)
                positions = service.get_positions(portfolio.id)

                portfolio_responses.append(PortfolioResponse(
                    id=portfolio.id,
                    portfolio_name=portfolio.portfolio_name,
                    description=portfolio.description,
                    cash_balance=portfolio.cash_balance,
                    is_active=portfolio.is_active,
                    portfolio_type=portfolio.portfolio_type,
                    update_frequency=portfolio.update_frequency,
                    created_at=portfolio.created_at,
                    updated_at=portfolio.updated_at,
                    total_invested=portfolio.initial_amount,
                    current_value=value_data['total_market_value'],  # 当前市值（仅持仓）
                    total_return=value_data['total_return'],
                    total_return_rate=value_data['total_return_rate'],
                    position_count=len(positions)
                ))
            except Exception as e:
                logger.warning(f"计算组合 {portfolio.id} 市值失败: {str(e)}")
                # 即使计算失败也返回基本信息
                portfolio_responses.append(PortfolioResponse(
                    id=portfolio.id,
                    portfolio_name=portfolio.portfolio_name,
                    description=portfolio.description,
                    cash_balance=portfolio.cash_balance,
                    is_active=portfolio.is_active,
                    portfolio_type=portfolio.portfolio_type,
                    update_frequency=portfolio.update_frequency,
                    created_at=portfolio.created_at,
                    updated_at=portfolio.updated_at,
                    total_invested=portfolio.initial_amount
                ))

        return PortfolioListResponse(
            total=len(portfolio_responses),
            data=portfolio_responses
        )

    except Exception as e:
        logger.error(f"获取组合列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取组合列表失败: {str(e)}"
        )


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse, summary="获取组合详情")
async def get_portfolio_detail(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    获取组合详细信息，包括持仓、交易记录和净值历史
    """
    try:
        service = PortfolioService(db)
        portfolio = service.get_portfolio(portfolio_id)

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"组合 {portfolio_id} 不存在"
            )

        # 获取组合价值
        value_data = service.calculate_portfolio_value(portfolio_id)

        # 获取持仓
        positions = service.get_positions(portfolio_id)
        position_responses = []
        for pos in positions:
            # 从value_data中查找对应的详情
            pos_detail = next((p for p in value_data['positions'] if p['fund_code'] == pos.fund_code), None)

            # 根据组合类型获取基金名称
            if portfolio.portfolio_type == 'private':
                fund = db.query(Fund).filter(Fund.fund_code == pos.fund_code).first()
                # 私募基金优先使用简称，如果没有简称则使用全名
                fund_display_name = (fund.short_name or fund.fund_name) if fund else None
            else:
                fund = db.query(PublicFund).filter(PublicFund.fund_code == pos.fund_code).first()
                fund_display_name = fund.fund_name if fund else None

            if pos_detail:
                # 计算权重
                weight = (pos_detail['current_value'] / value_data['total_market_value'] * 100) if value_data['total_market_value'] > 0 else Decimal('0')

                position_responses.append(PositionResponse(
                    id=pos.id,
                    portfolio_id=pos.portfolio_id,
                    fund_code=pos.fund_code,
                    fund_name=fund_display_name,
                    shares=pos.shares,
                    cost_amount=pos.cost_amount,
                    avg_cost_nav=pos.avg_cost_nav,
                    current_nav=pos_detail['current_nav'],
                    current_nav_date=pos_detail['current_nav_date'],
                    current_value=pos_detail['current_value'],
                    profit_loss=pos_detail['profit_loss'],
                    profit_loss_rate=pos_detail['profit_loss_rate'],
                    weight=weight,
                    created_at=pos.created_at,
                    updated_at=pos.updated_at
                ))

        # 获取交易记录
        transactions = service.get_transactions(portfolio_id, limit=100)
        transaction_responses = []
        for txn in transactions:
            # 根据组合类型获取基金名称
            if portfolio.portfolio_type == 'private':
                fund = db.query(Fund).filter(Fund.fund_code == txn.fund_code).first()
                # 私募基金优先使用简称，如果没有简称则使用全名
                fund_display_name = (fund.short_name or fund.fund_name) if fund else None
            else:
                fund = db.query(PublicFund).filter(PublicFund.fund_code == txn.fund_code).first()
                fund_display_name = fund.fund_name if fund else None

            transaction_responses.append(TransactionResponse(
                id=txn.id,
                portfolio_id=txn.portfolio_id,
                fund_code=txn.fund_code,
                fund_name=fund_display_name,
                transaction_type=txn.transaction_type,
                transaction_date=txn.transaction_date,
                amount=txn.amount,
                shares=txn.shares,
                nav=txn.nav,
                fee=txn.fee,
                note=txn.note,
                created_at=txn.created_at
            ))

        # 获取净值历史
        nav_history = service.get_nav_history(portfolio_id)
        nav_responses = [
            PortfolioNavResponse(
                id=nav.id,
                portfolio_id=nav.portfolio_id,
                nav_date=nav.nav_date,
                total_market_value=nav.total_market_value,
                cash_balance=nav.cash_balance,
                total_assets=nav.total_assets,
                daily_return=nav.daily_return,
                cumulative_return=nav.cumulative_return,
                cumulative_return_rate=nav.cumulative_return_rate,
                created_at=nav.created_at
            ) for nav in nav_history
        ]

        # 构建组合响应
        portfolio_response = PortfolioResponse(
            id=portfolio.id,
            portfolio_name=portfolio.portfolio_name,
            description=portfolio.description,
            cash_balance=portfolio.cash_balance,
            is_active=portfolio.is_active,
            portfolio_type=portfolio.portfolio_type,
            update_frequency=portfolio.update_frequency,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
            total_invested=portfolio.initial_amount,
            current_value=value_data['total_market_value'],  # 当前市值（仅持仓）
            total_return=value_data['total_return'],
            total_return_rate=value_data['total_return_rate'],
            position_count=len(positions)
        )

        return PortfolioDetailResponse(
            portfolio=portfolio_response,
            positions=position_responses,
            transactions=transaction_responses,
            nav_history=nav_responses,
            summary=value_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取组合详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取组合详情失败: {str(e)}"
        )


@router.put("/{portfolio_id}", response_model=PortfolioResponse, summary="更新组合")
async def update_portfolio(
    portfolio_id: int,
    update_data: PortfolioUpdate,
    db: Session = Depends(get_db)
):
    """
    更新组合信息
    """
    try:
        service = PortfolioService(db)
        updated_portfolio = service.update_portfolio(portfolio_id, update_data)

        # 计算当前市值
        value_data = service.calculate_portfolio_value(portfolio_id)
        positions = service.get_positions(portfolio_id)

        return PortfolioResponse(
            id=updated_portfolio.id,
            portfolio_name=updated_portfolio.portfolio_name,
            description=updated_portfolio.description,
            cash_balance=updated_portfolio.cash_balance,
            is_active=updated_portfolio.is_active,
            created_at=updated_portfolio.created_at,
            updated_at=updated_portfolio.updated_at,
            total_invested=updated_portfolio.initial_amount,
            current_value=value_data['total_market_value'],  # 当前市值（仅持仓）
            total_return=value_data['total_return'],
            total_return_rate=value_data['total_return_rate'],
            position_count=len(positions)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新组合失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新组合失败: {str(e)}"
        )


@router.delete("/{portfolio_id}", summary="删除组合")
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    删除组合（级联删除所有相关数据）
    """
    try:
        service = PortfolioService(db)
        service.delete_portfolio(portfolio_id)

        return {"success": True, "message": f"组合 {portfolio_id} 已删除"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除组合失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除组合失败: {str(e)}"
        )


# ========== 交易管理 ==========

@router.post("/{portfolio_id}/transaction", response_model=TransactionResponse, summary="添加交易")
async def add_transaction(
    portfolio_id: int,
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """
    添加交易记录（买入/卖出）
    """
    try:
        service = PortfolioService(db)
        new_transaction = service.add_transaction(portfolio_id, transaction)

        # 交易后自动保存净值快照
        service.save_portfolio_nav(portfolio_id, transaction.transaction_date)

        # 获取组合类型，根据类型查询基金名称
        portfolio = service.get_portfolio(portfolio_id)
        if portfolio.portfolio_type == 'private':
            fund = db.query(Fund).filter(Fund.fund_code == new_transaction.fund_code).first()
            # 私募基金优先使用简称，如果没有简称则使用全名
            fund_display_name = (fund.short_name or fund.fund_name) if fund else None
        else:
            fund = db.query(PublicFund).filter(PublicFund.fund_code == new_transaction.fund_code).first()
            fund_display_name = fund.fund_name if fund else None

        return TransactionResponse(
            id=new_transaction.id,
            portfolio_id=new_transaction.portfolio_id,
            fund_code=new_transaction.fund_code,
            fund_name=fund_display_name,
            transaction_type=new_transaction.transaction_type,
            transaction_date=new_transaction.transaction_date,
            amount=new_transaction.amount,
            shares=new_transaction.shares,
            nav=new_transaction.nav,
            fee=new_transaction.fee,
            note=new_transaction.note,
            created_at=new_transaction.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"添加交易失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加交易失败: {str(e)}"
        )


@router.get("/{portfolio_id}/transactions", response_model=List[TransactionResponse], summary="获取交易记录")
async def get_transactions(
    portfolio_id: int,
    limit: int = Query(100, description="返回记录数量"),
    db: Session = Depends(get_db)
):
    """
    获取组合的交易记录
    """
    try:
        service = PortfolioService(db)
        transactions = service.get_transactions(portfolio_id, limit)

        # 获取组合类型
        portfolio = service.get_portfolio(portfolio_id)

        transaction_responses = []
        for txn in transactions:
            # 根据组合类型查询基金名称
            if portfolio.portfolio_type == 'private':
                fund = db.query(Fund).filter(Fund.fund_code == txn.fund_code).first()
                # 私募基金优先使用简称，如果没有简称则使用全名
                fund_display_name = (fund.short_name or fund.fund_name) if fund else None
            else:
                fund = db.query(PublicFund).filter(PublicFund.fund_code == txn.fund_code).first()
                fund_display_name = fund.fund_name if fund else None

            transaction_responses.append(TransactionResponse(
                id=txn.id,
                portfolio_id=txn.portfolio_id,
                fund_code=txn.fund_code,
                fund_name=fund_display_name,
                transaction_type=txn.transaction_type,
                transaction_date=txn.transaction_date,
                amount=txn.amount,
                shares=txn.shares,
                nav=txn.nav,
                fee=txn.fee,
                note=txn.note,
                created_at=txn.created_at
            ))

        return transaction_responses

    except Exception as e:
        logger.error(f"获取交易记录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易记录失败: {str(e)}"
        )


@router.delete("/{portfolio_id}/transaction/{transaction_id}", summary="删除交易")
async def delete_transaction(
    portfolio_id: int,
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    删除交易记录（会回滚持仓和现金余额）
    """
    try:
        service = PortfolioService(db)
        service.delete_transaction(portfolio_id, transaction_id)

        return {"success": True, "message": f"交易记录 {transaction_id} 已删除"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除交易失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除交易失败: {str(e)}"
        )


# ========== 净值管理 ==========

@router.post("/{portfolio_id}/nav", summary="保存净值快照")
async def save_portfolio_nav(
    portfolio_id: int,
    nav_date: Optional[date] = Query(None, description="净值日期"),
    db: Session = Depends(get_db)
):
    """
    手动保存组合净值快照
    """
    try:
        service = PortfolioService(db)
        service.save_portfolio_nav(portfolio_id, nav_date)

        return {"success": True, "message": "净值快照已保存"}

    except Exception as e:
        logger.error(f"保存净值快照失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存净值快照失败: {str(e)}"
        )


@router.get("/{portfolio_id}/nav-history", response_model=List[PortfolioNavResponse], summary="获取净值历史")
async def get_nav_history(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取组合净值历史
    """
    try:
        service = PortfolioService(db)
        nav_history = service.get_nav_history(portfolio_id, start_date, end_date)

        return [
            PortfolioNavResponse(
                id=nav.id,
                portfolio_id=nav.portfolio_id,
                nav_date=nav.nav_date,
                total_market_value=nav.total_market_value,
                cash_balance=nav.cash_balance,
                total_assets=nav.total_assets,
                daily_return=nav.daily_return,
                cumulative_return=nav.cumulative_return,
                cumulative_return_rate=nav.cumulative_return_rate,
                created_at=nav.created_at
            ) for nav in nav_history
        ]

    except Exception as e:
        logger.error(f"获取净值历史失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取净值历史失败: {str(e)}"
        )
