"""
初始化数据脚本
Initialize Data Script
"""

from sqlalchemy.orm import Session
from .database import get_db
from .models import Fund, Strategy
import logging

logger = logging.getLogger(__name__)


def init_sample_data(db: Session):
    """初始化示例数据"""
    
    # 检查是否已有数据
    existing_funds = db.query(Fund).count()
    if existing_funds > 0:
        logger.info(f"数据库已有 {existing_funds} 个基金，跳过初始化")
        return
    
    # 示例基金数据
    sample_funds = [
        {"fund_code": "L03126", "fund_name": "精选成长基金"},
        {"fund_code": "L03127", "fund_name": "稳健收益基金"},
        {"fund_code": "L03128", "fund_name": "灵活配置基金"},
        {"fund_code": "L03129", "fund_name": "价值精选基金"},
        {"fund_code": "L03130", "fund_name": "量化策略基金"},
        {"fund_code": "L03131", "fund_name": "债券增强基金"},
        {"fund_code": "L03132", "fund_name": "科技创新基金"},
        {"fund_code": "L03133", "fund_name": "医疗健康基金"},
        {"fund_code": "L03134", "fund_name": "消费升级基金"},
        {"fund_code": "L03135", "fund_name": "新能源基金"}
    ]
    
    # 示例策略数据
    sample_strategies = [
        {"fund_code": "L03126", "major_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03127", "major_strategy": "fixed_income", "sub_strategy": "pure_bond", "is_qd": False},
        {"fund_code": "L03128", "major_strategy": "macro", "sub_strategy": "macro_hedge", "is_qd": True},
        {"fund_code": "L03129", "major_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03130", "major_strategy": "other", "sub_strategy": "market_neutral", "is_qd": True},
        {"fund_code": "L03131", "major_strategy": "fixed_income", "sub_strategy": "credit_bond", "is_qd": False},
        {"fund_code": "L03132", "major_strategy": "growth", "sub_strategy": "tech_growth", "is_qd": False},
        {"fund_code": "L03133", "major_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03134", "major_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03135", "major_strategy": "growth", "sub_strategy": "tech_growth", "is_qd": False}
    ]
    
    try:
        # 添加基金数据
        for fund_data in sample_funds:
            fund = Fund(**fund_data)
            db.add(fund)
        
        # 添加策略数据
        for strategy_data in sample_strategies:
            strategy = Strategy(**strategy_data)
            db.add(strategy)
        
        db.commit()
        logger.info(f"成功初始化 {len(sample_funds)} 个基金和 {len(sample_strategies)} 个策略")
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化数据失败: {str(e)}")
        raise


def init_data_if_needed():
    """如果需要则初始化数据"""
    try:
        db = next(get_db())
        init_sample_data(db)
        db.close()
    except Exception as e:
        logger.error(f"数据初始化异常: {str(e)}")