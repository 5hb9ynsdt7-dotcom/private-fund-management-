"""
数据库初始化和数据迁移工具
Database Initialization and Migration Utilities
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import db_manager, init_database
from .models import Fund, Strategy, Nav, Client, Position, DateConverter
from .models import validate_fund_code, validate_nav_data

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def initialize_fresh_database(self) -> bool:
        """
        初始化全新数据库
        删除现有数据并重新创建表结构
        """
        try:
            logger.info("开始初始化全新数据库...")
            
            # 重置数据库
            self.db_manager.reset_database()
            
            # 插入初始数据
            self.insert_sample_data()
            
            logger.info("数据库初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            return False
    
    def insert_sample_data(self):
        """插入示例数据"""
        logger.info("开始插入示例数据...")
        
        with self.db_manager.get_session() as session:
            try:
                # 1. 插入基金数据
                self._insert_sample_funds(session)
                
                # 2. 插入策略数据
                self._insert_sample_strategies(session)
                
                # 3. 插入净值数据
                self._insert_sample_nav(session)
                
                # 4. 插入客户数据
                self._insert_sample_clients(session)
                
                # 5. 插入持仓数据
                self._insert_sample_positions(session)
                
                logger.info("示例数据插入完成")
                
            except Exception as e:
                logger.error(f"插入示例数据失败: {str(e)}")
                raise
    
    def _insert_sample_funds(self, session: Session):
        """插入示例基金数据"""
        sample_funds = [
            Fund(
                fund_code="L03126",
                fund_name="歌斐全球价值配置6211私募证券投资基金直销A类"
            ),
            Fund(
                fund_code="L03127",
                fund_name="歌斐成长策略7310私募证券投资基金"
            ),
            Fund(
                fund_code="L03128",
                fund_name="歌斐固收稳健8412私募证券投资基金"
            )
        ]
        
        for fund in sample_funds:
            existing = session.query(Fund).filter_by(fund_code=fund.fund_code).first()
            if not existing:
                session.add(fund)
                logger.info(f"添加基金: {fund.fund_code} - {fund.fund_name}")
    
    def _insert_sample_strategies(self, session: Session):
        """插入示例策略数据"""
        sample_strategies = [
            Strategy(
                fund_code="L03126",
                project_name="全球价值配置项目",
                main_strategy="成长策略",
                sub_strategy="主观多头",
                is_qd=False
            ),
            Strategy(
                fund_code="L03127",
                project_name="成长策略项目",
                main_strategy="成长策略",
                sub_strategy="量化多头",
                is_qd=True
            ),
            Strategy(
                fund_code="L03128",
                project_name="固收稳健项目",
                main_strategy="固收策略",
                sub_strategy="债券投资",
                is_qd=False
            )
        ]
        
        for strategy in sample_strategies:
            existing = session.query(Strategy).filter_by(fund_code=strategy.fund_code).first()
            if not existing:
                session.add(strategy)
                logger.info(f"添加策略: {strategy.fund_code} - {strategy.main_strategy}")
    
    def _insert_sample_nav(self, session: Session):
        """插入示例净值数据"""
        sample_nav_data = [
            # L03126 净值数据
            {"fund_code": "L03126", "nav_date": "20250701", "unit_nav": 1.2580, "accum_nav": 1.2580},
            {"fund_code": "L03126", "nav_date": "20250702", "unit_nav": 1.2610, "accum_nav": 1.2610},
            {"fund_code": "L03126", "nav_date": "20250703", "unit_nav": 1.2595, "accum_nav": 1.2595},
            
            # L03127 净值数据
            {"fund_code": "L03127", "nav_date": "20250701", "unit_nav": 1.1820, "accum_nav": 1.3420},
            {"fund_code": "L03127", "nav_date": "20250702", "unit_nav": 1.1845, "accum_nav": 1.3445},
            
            # L03128 净值数据
            {"fund_code": "L03128", "nav_date": "20250701", "unit_nav": 1.0520, "accum_nav": 1.0520},
            {"fund_code": "L03128", "nav_date": "20250702", "unit_nav": 1.0525, "accum_nav": 1.0525},
        ]
        
        for nav_data in sample_nav_data:
            # 转换日期格式
            nav_date = DateConverter.convert_date_string(nav_data["nav_date"])
            
            # 验证净值数据
            is_valid, error_msg = validate_nav_data(nav_data["unit_nav"], nav_data["accum_nav"])
            if not is_valid:
                logger.warning(f"跳过无效净值数据: {nav_data}, 错误: {error_msg}")
                continue
            
            # 检查是否已存在
            existing = session.query(Nav).filter_by(
                fund_code=nav_data["fund_code"],
                nav_date=nav_date
            ).first()
            
            if not existing:
                nav_record = Nav(
                    fund_code=nav_data["fund_code"],
                    nav_date=nav_date,
                    unit_nav=Decimal(str(nav_data["unit_nav"])),
                    accum_nav=Decimal(str(nav_data["accum_nav"]))
                )
                session.add(nav_record)
                logger.info(f"添加净值: {nav_data['fund_code']} - {nav_date}")
    
    def _insert_sample_clients(self, session: Session):
        """插入示例客户数据"""
        sample_clients = [
            Client(
                group_id="000319506",
                obscured_name="邢*东",
                domestic_planner="张理财师"
            ),
            Client(
                group_id="000421789",
                obscured_name="李*华",
                domestic_planner="王理财师"
            ),
            Client(
                group_id="000521345",
                obscured_name="陈*明",
                domestic_planner="赵理财师"
            )
        ]
        
        for client in sample_clients:
            # 格式化集团号
            client.group_id = DateConverter.format_group_id(client.group_id)
            
            existing = session.query(Client).filter_by(group_id=client.group_id).first()
            if not existing:
                session.add(client)
                logger.info(f"添加客户: {client.group_id} - {client.obscured_name}")
    
    def _insert_sample_positions(self, session: Session):
        """插入示例持仓数据"""
        sample_positions = [
            {
                "group_id": "000319506",
                "fund_code": "L03126",
                "stock_date": "20250601",
                "cost_with_fee": 1000000.00,
                "cost_without_fee": 995000.00,
                "shares": 795238.10
            },
            {
                "group_id": "000319506",
                "fund_code": "L03127",
                "stock_date": "20250601",
                "cost_with_fee": 500000.00,
                "cost_without_fee": 497500.00,
                "shares": 423728.81
            },
            {
                "group_id": "000421789",
                "fund_code": "L03128",
                "stock_date": "20250615",
                "cost_with_fee": 2000000.00,
                "cost_without_fee": 1990000.00,
                "shares": 1900475.94
            }
        ]
        
        for pos_data in sample_positions:
            # 转换日期格式
            stock_date = DateConverter.convert_date_string(pos_data["stock_date"])
            
            # 格式化集团号
            group_id = DateConverter.format_group_id(pos_data["group_id"])
            
            # 检查是否已存在
            existing = session.query(Position).filter_by(
                group_id=group_id,
                fund_code=pos_data["fund_code"],
                stock_date=stock_date
            ).first()
            
            if not existing:
                position = Position(
                    group_id=group_id,
                    fund_code=pos_data["fund_code"],
                    stock_date=stock_date,
                    cost_with_fee=Decimal(str(pos_data["cost_with_fee"])),
                    cost_without_fee=Decimal(str(pos_data["cost_without_fee"])),
                    shares=Decimal(str(pos_data["shares"]))
                )
                session.add(position)
                logger.info(f"添加持仓: {group_id} - {pos_data['fund_code']}")


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_database_integrity(session: Session) -> Dict[str, Any]:
        """验证数据库完整性"""
        logger.info("开始验证数据库完整性...")
        
        validation_results = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # 1. 统计表记录数
            validation_results["stats"] = {
                "funds": session.query(Fund).count(),
                "strategies": session.query(Strategy).count(),
                "nav_records": session.query(Nav).count(),
                "clients": session.query(Client).count(),
                "positions": session.query(Position).count()
            }
            
            # 2. 检查外键完整性
            DataValidator._check_foreign_key_integrity(session, validation_results)
            
            # 3. 检查净值数据有效性
            DataValidator._check_nav_data_validity(session, validation_results)
            
            # 4. 检查唯一约束
            DataValidator._check_unique_constraints(session, validation_results)
            
            logger.info("数据库完整性验证完成")
            
        except Exception as e:
            validation_results["passed"] = False
            validation_results["errors"].append(f"验证过程异常: {str(e)}")
            logger.error(f"数据库完整性验证失败: {str(e)}")
        
        return validation_results
    
    @staticmethod
    def _check_foreign_key_integrity(session: Session, results: Dict):
        """检查外键完整性"""
        # 检查策略表外键
        strategies_without_fund = session.query(Strategy).filter(
            ~Strategy.fund_code.in_(session.query(Fund.fund_code))
        ).count()
        
        if strategies_without_fund > 0:
            results["errors"].append(f"发现 {strategies_without_fund} 条策略记录的基金代码不存在")
        
        # 检查净值表外键
        nav_without_fund = session.query(Nav).filter(
            ~Nav.fund_code.in_(session.query(Fund.fund_code))
        ).count()
        
        if nav_without_fund > 0:
            results["errors"].append(f"发现 {nav_without_fund} 条净值记录的基金代码不存在")
        
        # 检查持仓表外键
        positions_without_client = session.query(Position).filter(
            ~Position.group_id.in_(session.query(Client.group_id))
        ).count()
        
        if positions_without_client > 0:
            results["errors"].append(f"发现 {positions_without_client} 条持仓记录的客户不存在")
        
        positions_without_fund = session.query(Position).filter(
            ~Position.fund_code.in_(session.query(Fund.fund_code))
        ).count()
        
        if positions_without_fund > 0:
            results["errors"].append(f"发现 {positions_without_fund} 条持仓记录的基金代码不存在")
    
    @staticmethod
    def _check_nav_data_validity(session: Session, results: Dict):
        """检查净值数据有效性"""
        invalid_nav = session.query(Nav).filter(
            (Nav.unit_nav <= 0) | (Nav.accum_nav < Nav.unit_nav)
        ).count()
        
        if invalid_nav > 0:
            results["errors"].append(f"发现 {invalid_nav} 条无效净值记录（单位净值<=0 或 累计净值<单位净值）")
    
    @staticmethod
    def _check_unique_constraints(session: Session, results: Dict):
        """检查唯一约束"""
        # 检查基金代码唯一性（主键自动保证）
        
        # 检查策略表基金代码唯一性
        strategy_duplicates = session.query(Strategy.fund_code).group_by(Strategy.fund_code).having(
            func.count(Strategy.fund_code) > 1
        ).count()
        
        if strategy_duplicates > 0:
            results["errors"].append(f"发现 {strategy_duplicates} 个基金有重复的策略记录")


# 便捷函数
def initialize_database_with_sample_data() -> bool:
    """初始化数据库并插入示例数据"""
    initializer = DatabaseInitializer()
    return initializer.initialize_fresh_database()


def validate_database() -> Dict[str, Any]:
    """验证数据库完整性"""
    with db_manager.get_session() as session:
        return DataValidator.validate_database_integrity(session)


if __name__ == "__main__":
    # 命令行运行时执行初始化
    print("开始初始化私募基金管理系统数据库...")
    
    if initialize_database_with_sample_data():
        print("✅ 数据库初始化成功！")
        
        # 验证数据库
        validation = validate_database()
        if validation["passed"]:
            print("✅ 数据库验证通过！")
            print(f"📊 数据统计: {validation['stats']}")
        else:
            print("❌ 数据库验证失败！")
            for error in validation["errors"]:
                print(f"   错误: {error}")
    else:
        print("❌ 数据库初始化失败！")