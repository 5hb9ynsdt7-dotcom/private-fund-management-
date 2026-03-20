"""
组合回测路由
Portfolio Backtest Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime
import json

from ..database import get_db
from ..schemas.common import APIResponse
from ..services.portfolio_backtest_service import PortfolioBacktestService
from ..models import BacktestPortfolio

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/portfolio-backtest",
    tags=["组合回测"],
)

# 创建回测服务实例
backtest_service = PortfolioBacktestService()


class PortfolioItem(BaseModel):
    """组合中的单个产品"""
    fund_code: str
    weight: Optional[float] = None  # 权重（0-1），如果按权重配置
    amount: Optional[float] = None  # 金额（万元），如果按金额配置


class BacktestRequest(BaseModel):
    """回测请求模型"""
    portfolio: List[PortfolioItem]  # 组合列表
    initial_capital: float  # 初始资金（万元）
    start_date: str  # 开始日期 YYYY-MM-DD
    end_date: str  # 结束日期 YYYY-MM-DD
    benchmark: Optional[str] = None  # 对比基准（指数代码）
    benchmark_product: Optional[str] = None  # 对比基准（产品代码）
    rebalance_frequency: str = "quarterly"  # 调仓频率: none, monthly, quarterly, semiannual, annual
    reinvest_dividend: bool = True  # 是否分红再投资
    consider_fees: bool = True  # 是否考虑费用
    weight_mode: str = "weight"  # 配置模式: weight 或 amount


@router.post("/run", response_model=APIResponse, summary="运行组合回测")
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db)
):
    """
    运行组合回测

    - **portfolio**: 组合产品列表
    - **initial_capital**: 初始资金（万元）
    - **start_date**: 回测开始日期
    - **end_date**: 回测结束日期
    - **rebalance_frequency**: 调仓频率
    - **reinvest_dividend**: 是否分红再投资
    - **consider_fees**: 是否考虑费用
    - **weight_mode**: 配置模式（weight 或 amount）
    """
    try:
        # 验证输入
        if not request.portfolio or len(request.portfolio) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="组合不能为空"
            )

        if request.initial_capital <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="初始资金必须大于0"
            )

        # 验证权重配置
        if request.weight_mode == "weight":
            total_weight = sum(item.weight or 0 for item in request.portfolio)
            if abs(total_weight - 1.0) > 0.01:  # 允许1%的误差
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"权重总和必须等于100%，当前为{total_weight * 100:.2f}%"
                )

        # 运行回测
        result = await backtest_service.run_backtest(
            db=db,
            portfolio=request.portfolio,
            initial_capital=request.initial_capital,
            start_date=request.start_date,
            end_date=request.end_date,
            benchmark=request.benchmark,
            benchmark_product=request.benchmark_product,
            rebalance_frequency=request.rebalance_frequency,
            reinvest_dividend=request.reinvest_dividend,
            consider_fees=request.consider_fees,
            weight_mode=request.weight_mode
        )

        return APIResponse(
            success=True,
            message="回测完成",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回测失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回测失败: {str(e)}"
        )


class SavePortfolioRequest(BaseModel):
    """保存组合请求模型"""
    portfolio_name: str  # 组合名称
    portfolio: List[PortfolioItem]  # 组合列表
    initial_capital: float  # 初始资金（万元）
    weight_mode: str = "weight"  # 配置模式: weight 或 amount
    rebalance_frequency: str = "quarterly"  # 调仓频率
    reinvest_dividend: bool = True  # 是否分红再投资
    consider_fees: bool = True  # 是否考虑费用


@router.post("/save", response_model=APIResponse, summary="保存组合配置")
async def save_portfolio(
    request: SavePortfolioRequest,
    db: Session = Depends(get_db)
):
    """
    保存组合配置并运行回测

    - **portfolio_name**: 组合名称
    - **portfolio**: 组合产品列表
    - **initial_capital**: 初始资金
    - **weight_mode**: 配置模式
    - **rebalance_frequency**: 调仓频率
    - **reinvest_dividend**: 是否分红再投资
    - **consider_fees**: 是否考虑费用
    """
    try:
        if not request.portfolio_name or request.portfolio_name.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="组合名称不能为空"
            )

        if not request.portfolio or len(request.portfolio) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="组合不能为空"
            )

        # 将组合配置转换为JSON
        portfolio_config = {
            "items": [item.dict() for item in request.portfolio]
        }

        # 运行回测获取结果（用于业绩PK）
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')

        # 先保存组合配置，获取 ID
        new_portfolio = BacktestPortfolio(
            portfolio_name=request.portfolio_name.strip(),
            portfolio_config=json.dumps(portfolio_config, ensure_ascii=False),
            initial_capital=request.initial_capital,
            weight_mode=request.weight_mode,
            rebalance_frequency=request.rebalance_frequency,
            reinvest_dividend=request.reinvest_dividend,
            consider_fees=request.consider_fees,
            backtest_result=None  # 先设为 None，回测成功后更新
        )

        db.add(new_portfolio)
        db.commit()
        db.refresh(new_portfolio)

        # 运行回测并保存周度净值
        backtest_result_data = None
        try:
            backtest_result = await backtest_service.run_backtest(
                db=db,
                portfolio=request.portfolio,
                initial_capital=request.initial_capital,
                start_date=start_date,
                end_date=end_date,
                benchmark=None,
                benchmark_product=None,
                rebalance_frequency=request.rebalance_frequency,
                reinvest_dividend=request.reinvest_dividend,
                consider_fees=request.consider_fees,
                weight_mode=request.weight_mode,
                portfolio_id=new_portfolio.id,  # 传递组合 ID
                portfolio_name=new_portfolio.portfolio_name  # 传递组合名称
            )
            backtest_result_data = json.dumps(backtest_result, ensure_ascii=False)

            # 更新回测结果
            new_portfolio.backtest_result = backtest_result_data
            db.commit()

            logger.info(f"组合 '{request.portfolio_name}' 回测成功，周度净值已保存")
        except Exception as e:
            logger.warning(f"组合 '{request.portfolio_name}' 回测失败: {str(e)}，配置已保存但无回测结果")

        return APIResponse(
            success=True,
            message=f"组合 '{request.portfolio_name}' 保存成功",
            data={
                "id": new_portfolio.id,
                "portfolio_name": new_portfolio.portfolio_name
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"保存组合失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存组合失败: {str(e)}"
        )


@router.get("/portfolios", response_model=APIResponse, summary="获取组合列表")
async def get_portfolios(db: Session = Depends(get_db)):
    """
    获取所有保存的组合配置列表
    """
    try:
        portfolios = db.query(BacktestPortfolio).order_by(
            BacktestPortfolio.created_at.desc()
        ).all()

        result = []
        for portfolio in portfolios:
            # 解析组合配置
            config = json.loads(portfolio.portfolio_config)

            result.append({
                "id": portfolio.id,
                "portfolio_name": portfolio.portfolio_name,
                "initial_capital": float(portfolio.initial_capital) if portfolio.initial_capital else 0,
                "weight_mode": portfolio.weight_mode,
                "rebalance_frequency": portfolio.rebalance_frequency,
                "reinvest_dividend": portfolio.reinvest_dividend,
                "consider_fees": portfolio.consider_fees,
                "product_count": len(config.get("items", [])),
                "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
                "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None
            })

        return APIResponse(
            success=True,
            message=f"成功获取 {len(result)} 个组合",
            data=result
        )

    except Exception as e:
        logger.error(f"获取组合列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取组合列表失败: {str(e)}"
        )


@router.get("/portfolios/{portfolio_id}", response_model=APIResponse, summary="获取组合详情")
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定组合的详细配置
    """
    try:
        portfolio = db.query(BacktestPortfolio).filter(
            BacktestPortfolio.id == portfolio_id
        ).first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到ID为 {portfolio_id} 的组合"
            )

        # 解析组合配置
        config = json.loads(portfolio.portfolio_config)

        result = {
            "id": portfolio.id,
            "portfolio_name": portfolio.portfolio_name,
            "portfolio": config.get("items", []),
            "initial_capital": float(portfolio.initial_capital) if portfolio.initial_capital else 0,
            "weight_mode": portfolio.weight_mode,
            "rebalance_frequency": portfolio.rebalance_frequency,
            "reinvest_dividend": portfolio.reinvest_dividend,
            "consider_fees": portfolio.consider_fees,
            "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
            "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None
        }

        return APIResponse(
            success=True,
            message="获取组合详情成功",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取组合详情失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取组合详情失败: {str(e)}"
        )


@router.delete("/portfolios/{portfolio_id}", response_model=APIResponse, summary="删除组合")
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """
    删除指定的组合配置
    """
    try:
        portfolio = db.query(BacktestPortfolio).filter(
            BacktestPortfolio.id == portfolio_id
        ).first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到ID为 {portfolio_id} 的组合"
            )

        portfolio_name = portfolio.portfolio_name

        db.delete(portfolio)
        db.commit()

        return APIResponse(
            success=True,
            message=f"组合 '{portfolio_name}' 删除成功",
            data={"id": portfolio_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除组合失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除组合失败: {str(e)}"
        )
