"""
产品深度分析相关数据模型
Product Deep Analysis Models
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Numeric, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .models import Base


class PositionTypeEnum(enum.Enum):
    """仓位类型枚举"""
    LONG = "long"   # 多头
    SHORT = "short"  # 空头


class ProductSectorAllocation(Base):
    """
    产品行业配置表 - 存储产品的行业配置数据（多头和空头）
    """
    __tablename__ = 'product_sector_allocation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(20), ForeignKey('fund.fund_code', ondelete='CASCADE'),
                         nullable=False, comment='产品代码，如L02798')
    allocation_date = Column(Date, nullable=False, comment='配置日期（月末日期）')
    sector_name = Column(String(50), nullable=False, comment='行业名称（如：信息技术、材料、工业）')
    allocation_pct = Column(Numeric(10, 2), nullable=False, comment='配置百分比')
    position_type = Column(Enum(PositionTypeEnum), nullable=False, comment='仓位类型：long(多头)或short(空头)')
    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # 复合唯一约束：同一产品+日期+行业+仓位类型唯一
    __table_args__ = (
        UniqueConstraint('product_code', 'allocation_date', 'sector_name', 'position_type',
                        name='uk_product_date_sector_type'),
    )

    def __repr__(self):
        return f"<ProductSectorAllocation(product={self.product_code}, date={self.allocation_date}, sector={self.sector_name}, pct={self.allocation_pct}, type={self.position_type.value})>"


class ProductAnalysisSummary(Base):
    """
    产品分析摘要表 - 存储产品深度分析的核心要点
    """
    __tablename__ = 'product_analysis_summary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(20), ForeignKey('fund.fund_code', ondelete='CASCADE'),
                         nullable=False, unique=True, comment='产品代码，如L02798')

    # 核心亮点（最多5个）
    highlight_1 = Column(Text, comment='亮点1')
    highlight_2 = Column(Text, comment='亮点2')
    highlight_3 = Column(Text, comment='亮点3')
    highlight_4 = Column(Text, comment='亮点4')
    highlight_5 = Column(Text, comment='亮点5')

    # 主要风险（最多3个）
    risk_1 = Column(Text, comment='风险1')
    risk_2 = Column(Text, comment='风险2')
    risk_3 = Column(Text, comment='风险3')

    # 策略特征描述
    strategy_description = Column(Text, comment='策略特征描述')

    # 时间范围
    analysis_start_date = Column(Date, comment='分析起始日期')
    analysis_end_date = Column(Date, comment='分析截止日期')

    created_at = Column(DateTime, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    def __repr__(self):
        return f"<ProductAnalysisSummary(product={self.product_code})>"
