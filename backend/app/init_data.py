"""
初始化数据脚本
Initialize Data Script
"""

from sqlalchemy.orm import Session
from .database import get_db
from .models import Fund, Strategy, Nav, Client, Position, Dividend
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


def init_sample_data(db: Session):
    """初始化示例数据（仅在没有真实数据时使用）"""
    
    # 检查是否已有数据
    existing_funds = db.query(Fund).count()
    if existing_funds > 0:
        logger.info(f"发现真实数据：数据库已有 {existing_funds} 个基金，跳过初始化示例数据")
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
        {"fund_code": "L03126", "main_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03127", "main_strategy": "fixed_income", "sub_strategy": "pure_bond", "is_qd": False},
        {"fund_code": "L03128", "main_strategy": "macro", "sub_strategy": "macro_hedge", "is_qd": True},
        {"fund_code": "L03129", "main_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03130", "main_strategy": "other", "sub_strategy": "market_neutral", "is_qd": True},
        {"fund_code": "L03131", "main_strategy": "fixed_income", "sub_strategy": "credit_bond", "is_qd": False},
        {"fund_code": "L03132", "main_strategy": "growth", "sub_strategy": "tech_growth", "is_qd": False},
        {"fund_code": "L03133", "main_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03134", "main_strategy": "growth", "sub_strategy": "growth_stock", "is_qd": False},
        {"fund_code": "L03135", "main_strategy": "growth", "sub_strategy": "tech_growth", "is_qd": False}
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
        
        # 提交基金和策略数据
        db.commit()
        
        # 生成净值数据（最近30天）
        nav_data = []
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        for fund_data in sample_funds:
            fund_code = fund_data["fund_code"]
            # 生成初始净值
            base_unit_nav = Decimal("1.0000")
            base_accum_nav = Decimal("1.0000")
            
            current_date = start_date
            while current_date <= end_date:
                # 模拟净值波动（每日±1%）
                import random
                change_rate = Decimal(str(random.uniform(-0.01, 0.01)))
                base_unit_nav = base_unit_nav * (1 + change_rate)
                base_accum_nav = base_accum_nav * (1 + change_rate)
                
                # 确保净值精度
                base_unit_nav = round(base_unit_nav, 6)
                base_accum_nav = round(base_accum_nav, 6)
                
                nav_data.append({
                    "fund_code": fund_code,
                    "nav_date": current_date,
                    "unit_nav": base_unit_nav,
                    "accum_nav": base_accum_nav
                })
                current_date += timedelta(days=1)
        
        # 添加净值数据
        for nav_item in nav_data:
            nav = Nav(**nav_item)
            db.add(nav)
        
        # 添加客户数据
        sample_clients = [
            {"group_id": "000319506", "obscured_name": "邢*东", "domestic_planner": "张理财师"},
            {"group_id": "000319507", "obscured_name": "李*明", "domestic_planner": "王理财师"},
            {"group_id": "000319508", "obscured_name": "王*华", "domestic_planner": "张理财师"},
            {"group_id": "000319509", "obscured_name": "陈*芳", "domestic_planner": "李理财师"},
            {"group_id": "000319510", "obscured_name": "刘*军", "domestic_planner": "王理财师"}
        ]
        
        for client_data in sample_clients:
            client = Client(**client_data)
            db.add(client)
        
        db.commit()
        logger.info(f"成功初始化 {len(sample_funds)} 个基金、{len(sample_strategies)} 个策略、{len(nav_data)} 条净值记录和 {len(sample_clients)} 个客户")
        
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