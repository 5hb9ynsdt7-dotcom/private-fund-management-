"""
数据库模型定义
Private Fund Management System Database Models
"""

from sqlalchemy import Column, String, Integer, Date, Boolean, ForeignKey, UniqueConstraint, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import re

Base = declarative_base()


class Fund(Base):
    """
    基金主表 - 存储基金基本信息
    """
    __tablename__ = 'fund'

    fund_code = Column(String(20), primary_key=True, comment='基金代码，如L03126')
    fund_name = Column(String(100), nullable=False, comment='基金全名')
    
    # 建立与其他表的关系
    strategy = relationship("Strategy", back_populates="fund", cascade="all, delete-orphan", uselist=False)
    nav_records = relationship("Nav", back_populates="fund", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="fund", cascade="all, delete-orphan")
    dividends = relationship("Dividend", back_populates="fund", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Fund(code='{self.fund_code}', name='{self.fund_name}')>"


class Strategy(Base):
    """
    策略表 - 存储基金投资策略信息
    """
    __tablename__ = 'strategy'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(20), ForeignKey('fund.fund_code', ondelete='CASCADE'), 
                      nullable=False, unique=True, comment='关联基金代码')
    project_name = Column(String(50), comment='项目名称')
    main_strategy = Column(String(30), comment='大类策略：成长策略/固收策略/宏观策略/其他')
    sub_strategy = Column(String(30), comment='细分策略：主观多头/量化多头等')
    is_qd = Column(Boolean, default=False, comment='是否QD产品')
    
    # 建立与基金表的关系
    fund = relationship("Fund", back_populates="strategy")
    
    def __repr__(self):
        return f"<Strategy(fund_code='{self.fund_code}', main_strategy='{self.main_strategy}')>"


class Nav(Base):
    """
    净值表 - 存储基金净值数据
    """
    __tablename__ = 'nav'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(20), ForeignKey('fund.fund_code', ondelete='CASCADE'), 
                      nullable=False, comment='关联基金代码')
    nav_date = Column(Date, nullable=False, comment='净值日期')
    unit_nav = Column(Numeric(16, 6), nullable=False, comment='单位净值')
    accum_nav = Column(Numeric(16, 6), nullable=False, comment='累计净值')
    
    # 建立与基金表的关系
    fund = relationship("Fund", back_populates="nav_records")
    
    # 复合唯一约束：同一基金同一日期只能有一条净值记录
    __table_args__ = (
        UniqueConstraint('fund_code', 'nav_date', name='uk_fund_nav_date'),
    )
    
    def __repr__(self):
        return f"<Nav(fund_code='{self.fund_code}', date='{self.nav_date}', unit_nav={self.unit_nav})>"
    
    @classmethod
    def validate_nav_values(cls, unit_nav: float, accum_nav: float) -> bool:
        """
        验证净值数据：累计净值 >= 单位净值 > 0
        """
        return unit_nav > 0 and accum_nav >= unit_nav


class Client(Base):
    """
    客户主表 - 存储客户基本信息
    """
    __tablename__ = 'client'

    group_id = Column(String(20), primary_key=True, comment='集团号，保留前导零如000319506')
    obscured_name = Column(String(10), comment='遮蔽姓名，如邢*东')
    domestic_planner = Column(String(50), comment='国内理财师')
    
    # 建立与其他表的关系
    positions = relationship("Position", back_populates="client", cascade="all, delete-orphan")
    dividend_records = relationship("ClientDividend", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Client(group_id='{self.group_id}', name='{self.obscured_name}')>"


class Position(Base):
    """
    持仓表 - 存储客户基金持仓信息
    """
    __tablename__ = 'position'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(20), ForeignKey('client.group_id', ondelete='CASCADE'), 
                     nullable=False, comment='关联客户集团号')
    fund_code = Column(String(20), ForeignKey('fund.fund_code', ondelete='CASCADE'), 
                      nullable=False, comment='关联基金代码')
    stock_date = Column(Date, nullable=False, comment='存量时间')
    first_buy_date = Column(Date, comment='首次买入日期')
    cost_with_fee = Column(Numeric(16, 2), comment='含费成本')
    cost_without_fee = Column(Numeric(16, 2), comment='不含费金额')
    shares = Column(Numeric(16, 2), comment='持仓份额')
    
    # 建立与客户表和基金表的关系
    client = relationship("Client", back_populates="positions")
    fund = relationship("Fund", back_populates="positions")
    
    # 复合唯一约束：同一客户+基金+存量时间唯一
    __table_args__ = (
        UniqueConstraint('group_id', 'fund_code', 'stock_date', name='uk_client_fund_date'),
    )
    
    def __repr__(self):
        return f"<Position(group_id='{self.group_id}', fund_code='{self.fund_code}', shares={self.shares})>"


# 工具函数：日期格式转换
class Dividend(Base):
    """
    分红表 - 存储基金分红信息
    """
    __tablename__ = 'dividend'

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(20), ForeignKey('fund.fund_code', ondelete='CASCADE'), 
                      nullable=False, comment='关联基金代码')
    dividend_date = Column(Date, nullable=False, comment='分红发放日期')
    dividend_per_share = Column(Numeric(16, 6), nullable=False, comment='每份分红金额')
    ex_dividend_date = Column(Date, comment='除息日')
    record_date = Column(Date, comment='登记日')
    
    # 建立与基金表的关系
    fund = relationship("Fund", back_populates="dividends")
    
    # 复合唯一约束：同一基金同一分红日期只能有一条记录
    __table_args__ = (
        UniqueConstraint('fund_code', 'dividend_date', name='uk_fund_dividend_date'),
    )
    
    def __repr__(self):
        return f"<Dividend(fund_code='{self.fund_code}', date='{self.dividend_date}', amount={self.dividend_per_share})>"
    
    @classmethod
    def validate_dividend_data(cls, dividend_per_share: float, dividend_date: date) -> tuple[bool, str]:
        """
        验证分红数据
        返回: (是否有效, 错误信息)
        """
        if dividend_per_share <= 0:
            return False, "分红金额必须大于0"
        
        if dividend_date > date.today():
            return False, "分红日期不能是未来日期"
        
        return True, ""


class ClientDividend(Base):
    """
    客户分红记录表 - 存储客户级别的分红交易记录
    """
    __tablename__ = 'client_dividend'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(20), ForeignKey('client.group_id', ondelete='CASCADE'), 
                     nullable=False, comment='关联客户集团号')
    fund_code = Column(String(20), ForeignKey('fund.fund_code', ondelete='CASCADE'), 
                      nullable=False, comment='关联基金代码')
    transaction_type = Column(String(20), nullable=False, comment='交易类型：现金红利/红利转投')
    confirmed_amount = Column(Numeric(16, 2), comment='确认金额(原币)')
    confirmed_shares = Column(Numeric(16, 6), comment='确认份额')
    confirmed_date = Column(Date, nullable=False, comment='确认日期')
    
    # 建立与客户表和基金表的关系
    client = relationship("Client", back_populates="dividend_records")
    fund = relationship("Fund", backref="client_dividends")
    
    # 复合唯一约束：同一客户同一基金同一确认日期同一类型只能有一条记录
    __table_args__ = (
        UniqueConstraint('group_id', 'fund_code', 'confirmed_date', 'transaction_type', 
                        name='uk_client_dividend_record'),
    )
    
    def __repr__(self):
        return f"<ClientDividend(group_id='{self.group_id}', fund_code='{self.fund_code}', type='{self.transaction_type}', amount={self.confirmed_amount})>"


class Transaction(Base):
    """
    交易表 - 存储客户基金交易记录，用于交易分析模块
    """
    __tablename__ = 'transaction'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(String(20), nullable=False, comment='集团号')
    client_name = Column(String(50), comment='客户遮蔽姓名')
    fund_name = Column(String(100), comment='基金名称')
    transaction_type = Column(String(30), nullable=False, comment='交易类型名称')
    confirmed_date = Column(Date, nullable=False, comment='交易确认日期')
    confirmed_shares = Column(Numeric(16, 6), comment='确认份额')
    confirmed_amount = Column(Numeric(16, 2), comment='确认金额')
    transaction_fee = Column(Numeric(16, 2), default=0, comment='手续费')
    product_code = Column(String(30), comment='产品代码')
    product_name = Column(String(100), comment='产品名称')
    
    # 外键关系
    # 注意：这里不使用外键约束，因为交易数据可能包含系统中不存在的基金或客户
    # 这样设计更灵活，适合数据分析场景
    
    # 为常见查询添加索引，提高查询性能
    # 注意：SQLAlchemy会根据这些字段组合自动创建索引
    
    def __repr__(self):
        return f"<Transaction(group_id='{self.group_id}', type='{self.transaction_type}', amount={self.confirmed_amount})>"
    
    @classmethod
    def validate_transaction_data(cls, data: dict) -> tuple[bool, list[str]]:
        """
        验证交易数据
        返回: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 必填字段验证
        required_fields = ['group_id', 'transaction_type', 'confirmed_date']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"缺少必填字段: {field}")
        
        # 集团号格式验证（应为数字）
        group_id = data.get('group_id')
        if group_id and not str(group_id).strip().isdigit():
            errors.append("集团号必须为数字")
        
        # 金额字段验证（如果存在）
        numeric_fields = ['confirmed_shares', 'confirmed_amount', 'transaction_fee']
        for field in numeric_fields:
            value = data.get(field)
            if value is not None:
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"{field}必须为有效数字")
        
        # 日期验证
        confirmed_date = data.get('confirmed_date')
        if confirmed_date:
            try:
                if isinstance(confirmed_date, str):
                    DateConverter.convert_date_string(confirmed_date)
            except ValueError as e:
                errors.append(f"交易确认日期格式错误: {str(e)}")
        
        return len(errors) == 0, errors


class ProjectHoldingAsset(Base):
    """
    项目持仓资产表 - 存储项目资产类别配置数据
    """
    __tablename__ = 'project_holding_asset'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(50), nullable=False, comment='项目名称')
    month = Column(Date, nullable=False, comment='月份')
    a_share_ratio = Column(Numeric(5, 2), comment='A股比例')
    h_share_ratio = Column(Numeric(5, 2), comment='H股比例') 
    us_share_ratio = Column(Numeric(5, 2), comment='美股比例')
    other_market_ratio = Column(Numeric(5, 2), comment='其他市场比例')
    stock_total_ratio = Column(Numeric(5, 2), comment='股票总仓位比例(计算字段)')
    global_bond_ratio = Column(Numeric(5, 2), comment='全球债券比例')
    convertible_bond_ratio = Column(Numeric(5, 2), comment='可转债比例')
    other_ratio = Column(Numeric(5, 2), comment='其他比例')
    created_at = Column(Date, default=func.current_date(), comment='创建时间')
    
    # 复合唯一约束：同一项目同一月份只能有一条资产配置记录
    __table_args__ = (
        UniqueConstraint('project_name', 'month', name='uk_project_asset_month'),
    )
    
    def __repr__(self):
        return f"<ProjectHoldingAsset(project='{self.project_name}', month='{self.month}', stock_total={self.stock_total_ratio})>"
    
    @classmethod
    def calculate_stock_total_ratio(cls, a_share: float = 0, h_share: float = 0, 
                                   us_share: float = 0, other_market: float = 0) -> float:
        """计算股票总仓位比例"""
        return (a_share or 0) + (h_share or 0) + (us_share or 0) + (other_market or 0)


class ProjectHoldingIndustry(Base):
    """
    项目持仓行业表 - 存储项目行业分类配置数据
    """
    __tablename__ = 'project_holding_industry'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(50), nullable=False, comment='项目名称')
    month = Column(Date, nullable=False, comment='月份')
    ratio_type = Column(String(20), nullable=False, comment='行业比例计算方式: based_on_stock/based_on_total')
    industry1 = Column(String(50), comment='第一持仓行业')
    industry1_ratio = Column(Numeric(5, 2), comment='第一持仓行业比例')
    industry2 = Column(String(50), comment='第二持仓行业')
    industry2_ratio = Column(Numeric(5, 2), comment='第二持仓行业比例')
    industry3 = Column(String(50), comment='第三持仓行业')
    industry3_ratio = Column(Numeric(5, 2), comment='第三持仓行业比例')
    industry4 = Column(String(50), comment='第四持仓行业')
    industry4_ratio = Column(Numeric(5, 2), comment='第四持仓行业比例')
    industry5 = Column(String(50), comment='第五持仓行业')
    industry5_ratio = Column(Numeric(5, 2), comment='第五持仓行业比例')
    created_at = Column(Date, default=func.current_date(), comment='创建时间')
    
    # 复合唯一约束：同一项目同一月份只能有一条行业配置记录
    __table_args__ = (
        UniqueConstraint('project_name', 'month', name='uk_project_industry_month'),
    )
    
    def __repr__(self):
        return f"<ProjectHoldingIndustry(project='{self.project_name}', month='{self.month}', ratio_type='{self.ratio_type}')>"
    
    @classmethod
    def validate_ratio_type(cls, ratio_type: str) -> bool:
        """验证行业比例计算方式"""
        return ratio_type in ['based_on_stock', 'based_on_total']
    
    def get_industries_with_ratios(self) -> list[tuple[str, float]]:
        """获取所有非空的行业及其比例"""
        industries = []
        for i in range(1, 6):
            industry_name = getattr(self, f'industry{i}')
            industry_ratio = getattr(self, f'industry{i}_ratio')
            if industry_name and industry_ratio:
                industries.append((industry_name, float(industry_ratio)))
        return industries
    
    def calculate_actual_ratios(self, stock_total_ratio: float) -> dict[str, float]:
        """
        计算行业实际占总仓位的比例
        :param stock_total_ratio: 股票总仓位比例，用于based_on_stock类型的计算
        :return: {行业名称: 实际比例}
        """
        actual_ratios = {}
        industries = self.get_industries_with_ratios()
        
        for industry_name, industry_ratio in industries:
            if self.ratio_type == 'based_on_stock':
                # 基于股票仓位计算：行业实际占比 = 行业比例 × 股票总仓位比例
                actual_ratio = industry_ratio * stock_total_ratio / 100
            else:  # based_on_total
                # 基于总仓位：行业比例直接表示占总仓位的比例
                actual_ratio = industry_ratio
            
            actual_ratios[industry_name] = actual_ratio
            
        return actual_ratios


class DateConverter:
    """
    日期格式转换工具类
    支持多种日期格式转换为标准DATE类型
    """
    
    @staticmethod
    def convert_date_string(date_str: str) -> date:
        """
        将各种格式的日期字符串转换为date对象
        支持格式：
        - 20250701 -> 2025-07-01
        - "2025年7月1日" -> 2025-07-01
        - "2025-07-01" -> 2025-07-01
        """
        if not date_str:
            raise ValueError("日期字符串不能为空")
        
        # 去除空格
        date_str = str(date_str).strip()
        
        # 格式1: 20250701 (8位数字)
        if re.match(r'^\d{8}$', date_str):
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            return date(year, month, day)
        
        # 格式2: 2025年7月1日
        if '年' in date_str and '月' in date_str and '日' in date_str:
            # 提取年月日
            year_match = re.search(r'(\d{4})年', date_str)
            month_match = re.search(r'(\d{1,2})月', date_str)
            day_match = re.search(r'(\d{1,2})日', date_str)
            
            if year_match and month_match and day_match:
                year = int(year_match.group(1))
                month = int(month_match.group(1))
                day = int(day_match.group(1))
                return date(year, month, day)
        
        # 格式3: 2025-07-01 或 2025/07/01 或 2025-08-15 00:00:00
        try:
            # 尝试使用datetime.strptime解析
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
        except:
            pass
        
        raise ValueError(f"不支持的日期格式: {date_str}")
    
    @staticmethod
    def format_group_id(group_id: str) -> str:
        """
        格式化集团号，确保前导零不丢失
        """
        if not group_id:
            return group_id
        
        # 确保是字符串类型
        group_id_str = str(group_id).strip()
        
        # 如果是纯数字，补齐到指定长度（如9位）
        if group_id_str.isdigit():
            return group_id_str.zfill(9)  # 补齐到9位
        
        return group_id_str


# 数据验证函数
def validate_fund_code(fund_code: str) -> bool:
    """验证基金代码格式"""
    if not fund_code:
        return False
    return len(fund_code) <= 20 and fund_code.isalnum()


def validate_nav_data(unit_nav: float, accum_nav: float) -> tuple[bool, str]:
    """
    验证净值数据
    返回: (是否有效, 错误信息)
    """
    if unit_nav <= 0:
        return False, "单位净值必须大于0"
    
    if accum_nav < unit_nav:
        return False, "累计净值必须大于等于单位净值"
    
    return True, ""


# 数据库表创建顺序（考虑外键依赖）
TABLES_CREATION_ORDER = [
    Fund,                   # 基金主表（无外键依赖）
    Client,                 # 客户主表（无外键依赖）
    Strategy,               # 策略表（依赖Fund）
    Nav,                    # 净值表（依赖Fund）
    Position,               # 持仓表（依赖Client和Fund）
    Dividend,               # 分红表（依赖Fund）
    ClientDividend,         # 客户分红表（依赖Client和Fund）
    Transaction,            # 交易表（无外键依赖，独立存储）
    ProjectHoldingAsset,    # 项目持仓资产表（无外键依赖）
    ProjectHoldingIndustry, # 项目持仓行业表（无外键依赖）
]