"""
导入磐泽扬帆精选6号的行业配置数据和分析摘要
"""

import sys
from datetime import date
from sqlalchemy.orm import Session

# 添加父目录到路径以导入app模块
sys.path.append('/Users/sudan/Desktop/Private Fund/privatefund/backend')

from app.database import db_manager
from app.models_product_analysis import ProductSectorAllocation, ProductAnalysisSummary, PositionTypeEnum

# 产品代码
PRODUCT_CODE = "L02798"

# 行业配置数据（来自行业配置数据表格.md）
# 格式: (日期, 行业名称, 配置百分比, 仓位类型)
sector_data = [
    # 2025年1月
    ('2025-01-31', '信息技术', 24.3, 'LONG'),
    ('2025-01-31', '材料', 3.2, 'LONG'),
    ('2025-01-31', '工业', 21.1, 'LONG'),
    ('2025-01-31', '半导体', 24.5, 'LONG'),
    ('2025-01-31', '金融', 14.1, 'LONG'),
    ('2025-01-31', '能源', 8.0, 'LONG'),
    ('2025-01-31', '房地产', 4.7, 'LONG'),

    # 2025年2月
    ('2025-02-28', '信息技术', 23.7, 'LONG'),
    ('2025-02-28', '材料', 3.3, 'LONG'),
    ('2025-02-28', '工业', 21.8, 'LONG'),
    ('2025-02-28', '半导体', 10.6, 'LONG'),
    ('2025-02-28', '金融', 23.5, 'LONG'),
    ('2025-02-28', '能源', 14.4, 'LONG'),
    ('2025-02-28', '公用事业', 2.7, 'LONG'),

    # 2025年3月
    ('2025-03-31', '信息技术', 44.4, 'LONG'),
    ('2025-03-31', '材料', 7.6, 'LONG'),
    ('2025-03-31', '工业', 13.7, 'LONG'),
    ('2025-03-31', '半导体', 10.2, 'LONG'),
    ('2025-03-31', '金融', 18.4, 'LONG'),
    ('2025-03-31', '能源', 5.6, 'LONG'),
    ('2025-03-31', '公用事业', 0.1, 'LONG'),

    # 2025年4月
    ('2025-04-30', '信息技术', 54.5, 'LONG'),
    ('2025-04-30', '材料', 23.6, 'LONG'),
    ('2025-04-30', '工业', 12.2, 'LONG'),
    ('2025-04-30', '半导体', 5.5, 'LONG'),
    ('2025-04-30', '能源', 10.3, 'LONG'),
    ('2025-04-30', '金融', 5.5, 'SHORT'),
    ('2025-04-30', '公用事业', 0.6, 'SHORT'),

    # 2025年5月
    ('2025-05-31', '信息技术', 39.3, 'LONG'),
    ('2025-05-31', '材料', 30.9, 'LONG'),
    ('2025-05-31', '工业', 15.6, 'LONG'),
    ('2025-05-31', '能源', 16.1, 'LONG'),
    ('2025-05-31', '金融', 0.4, 'SHORT'),
    ('2025-05-31', '公用事业', 1.4, 'SHORT'),

    # 2025年6月
    ('2025-06-30', '信息技术', 45.5, 'LONG'),
    ('2025-06-30', '材料', 21.8, 'LONG'),
    ('2025-06-30', '工业', 9.8, 'LONG'),
    ('2025-06-30', '半导体', 2.0, 'LONG'),
    ('2025-06-30', '金融', 3.8, 'LONG'),
    ('2025-06-30', '能源', 12.9, 'LONG'),
    ('2025-06-30', '可选消费', 5.1, 'LONG'),
    ('2025-06-30', '公用事业', 0.9, 'SHORT'),

    # 2025年7月
    ('2025-07-31', '信息技术', 62.2, 'LONG'),
    ('2025-07-31', '材料', 15.2, 'LONG'),
    ('2025-07-31', '工业', 9.1, 'LONG'),
    ('2025-07-31', '半导体', 5.9, 'LONG'),
    ('2025-07-31', '金融', 0.1, 'LONG'),
    ('2025-07-31', '能源', 10.7, 'LONG'),
    ('2025-07-31', '可选消费', 3.1, 'SHORT'),

    # 2025年8月
    ('2025-08-31', '信息技术', 73.2, 'LONG'),
    ('2025-08-31', '材料', 14.0, 'LONG'),
    ('2025-08-31', '工业', 5.3, 'LONG'),
    ('2025-08-31', '半导体', 17.8, 'LONG'),
    ('2025-08-31', '能源', 7.1, 'LONG'),
    ('2025-08-31', '可选消费', 0.5, 'LONG'),
    ('2025-08-31', '指数', 17.9, 'SHORT'),

    # 2025年9月
    ('2025-09-30', '信息技术', 67.1, 'LONG'),
    ('2025-09-30', '材料', 26.1, 'LONG'),
    ('2025-09-30', '工业', 3.1, 'LONG'),
    ('2025-09-30', '半导体', 4.3, 'LONG'),
    ('2025-09-30', '能源', 4.3, 'LONG'),
    ('2025-09-30', '可选消费', 16.6, 'SHORT'),
    ('2025-09-30', '指数', 1.7, 'SHORT'),

    # 2025年10月
    ('2025-10-31', '信息技术', 60.0, 'LONG'),
    ('2025-10-31', '材料', 30.1, 'LONG'),
    ('2025-10-31', '工业', 8.9, 'LONG'),
    ('2025-10-31', '半导体', 22.9, 'LONG'),
    ('2025-10-31', '能源', 2.8, 'LONG'),
    ('2025-10-31', '公用事业', 0.8, 'LONG'),
    ('2025-10-31', '可选消费', 4.0, 'SHORT'),
    ('2025-10-31', '指数', 21.4, 'SHORT'),

    # 2025年11月
    ('2025-11-30', '信息技术', 72.3, 'LONG'),
    ('2025-11-30', '材料', 28.4, 'LONG'),
    ('2025-11-30', '工业', 4.2, 'LONG'),
    ('2025-11-30', '半导体', 2.0, 'LONG'),
    ('2025-11-30', '能源', 2.6, 'LONG'),
    ('2025-11-30', '可选消费', 5.8, 'SHORT'),
    ('2025-11-30', '指数', 3.6, 'SHORT'),

    # 2025年12月
    ('2025-12-31', '信息技术', 58.3, 'LONG'),
    ('2025-12-31', '材料', 36.0, 'LONG'),
    ('2025-12-31', '工业', 7.4, 'LONG'),
    ('2025-12-31', '半导体', 1.3, 'LONG'),
    ('2025-12-31', '金融', 2.3, 'LONG'),
    ('2025-12-31', '能源', 2.5, 'LONG'),
    ('2025-12-31', '公用事业', 2.6, 'SHORT'),
    ('2025-12-31', '可选消费', 5.1, 'SHORT'),

    # 2026年1月
    ('2026-01-31', '信息技术', 60.4, 'LONG'),
    ('2026-01-31', '材料', 38.9, 'LONG'),
    ('2026-01-31', '工业', 9.2, 'LONG'),
    ('2026-01-31', '公用事业', 3.5, 'SHORT'),
    ('2026-01-31', '可选消费', 5.0, 'SHORT'),

    # 2026年2月
    ('2026-02-28', '信息技术', 57.2, 'LONG'),
    ('2026-02-28', '材料', 37.5, 'LONG'),
    ('2026-02-28', '工业', 13.4, 'LONG'),
    ('2026-02-28', '半导体', 0.2, 'LONG'),
    ('2026-02-28', '金融', 0.5, 'LONG'),
    ('2026-02-28', '公用事业', 3.5, 'SHORT'),
    ('2026-02-28', '可选消费', 5.3, 'SHORT'),
]

# 分析摘要数据（来自完整分析报告.md）
analysis_summary = {
    'highlights': [
        '趋势把握精准：提前布局信息技术和材料板块，完整捕获2025年中期的科技材料行情',
        '空头运用得当：在行情高位引入指数空头，有效控制回撤风险',
        '仓位集中有效：集中度提升（信息技术从24%→73%）是超额收益的核心来源',
        '14个月累计翻倍以上：从1.62到3.72，综合表现出色'
    ],
    'risks': [
        '集中度风险：信息技术单一仓位最高达73%，集中度较高',
        '策略容量限制：高集中度策略在资金规模扩大后可能面临冲击成本上升',
        '行情依赖性：业绩高度依赖信息技术和材料板块行情，一旦行情反转面临较大压力'
    ],
    'strategy_description': '多空股票型策略，以信息技术和材料板块为核心多头，配合指数/行业空头对冲，通过高集中度配置和灵活的多空调整获取超额收益',
    'analysis_start_date': date(2025, 1, 1),
    'analysis_end_date': date(2026, 2, 28)
}


def import_sector_allocation_data(db: Session):
    """导入行业配置数据"""
    print(f"\n开始导入 {PRODUCT_CODE} 的行业配置数据...")

    imported_count = 0
    skipped_count = 0

    for allocation_date, sector_name, allocation_pct, position_type in sector_data:
        # 检查是否已存在
        existing = db.query(ProductSectorAllocation).filter(
            ProductSectorAllocation.product_code == PRODUCT_CODE,
            ProductSectorAllocation.allocation_date == allocation_date,
            ProductSectorAllocation.sector_name == sector_name,
            ProductSectorAllocation.position_type == PositionTypeEnum[position_type]
        ).first()

        if existing:
            skipped_count += 1
            continue

        # 创建新记录
        allocation = ProductSectorAllocation(
            product_code=PRODUCT_CODE,
            allocation_date=date.fromisoformat(allocation_date),
            sector_name=sector_name,
            allocation_pct=allocation_pct,
            position_type=PositionTypeEnum[position_type]
        )
        db.add(allocation)
        imported_count += 1

    db.commit()
    print(f"✓ 导入完成：新增 {imported_count} 条记录，跳过 {skipped_count} 条已存在记录")


def import_analysis_summary(db: Session):
    """导入分析摘要"""
    print(f"\n开始导入 {PRODUCT_CODE} 的分析摘要...")

    # 检查是否已存在
    existing = db.query(ProductAnalysisSummary).filter(
        ProductAnalysisSummary.product_code == PRODUCT_CODE
    ).first()

    if existing:
        print("分析摘要已存在，正在更新...")
        # 更新现有记录
        for i, highlight in enumerate(analysis_summary['highlights'][:5], 1):
            setattr(existing, f'highlight_{i}', highlight)
        for i, risk in enumerate(analysis_summary['risks'][:3], 1):
            setattr(existing, f'risk_{i}', risk)
        existing.strategy_description = analysis_summary['strategy_description']
        existing.analysis_start_date = analysis_summary['analysis_start_date']
        existing.analysis_end_date = analysis_summary['analysis_end_date']
        action = "更新"
    else:
        print("创建新的分析摘要...")
        # 创建新记录
        summary = ProductAnalysisSummary(
            product_code=PRODUCT_CODE,
            strategy_description=analysis_summary['strategy_description'],
            analysis_start_date=analysis_summary['analysis_start_date'],
            analysis_end_date=analysis_summary['analysis_end_date']
        )

        for i, highlight in enumerate(analysis_summary['highlights'][:5], 1):
            setattr(summary, f'highlight_{i}', highlight)
        for i, risk in enumerate(analysis_summary['risks'][:3], 1):
            setattr(summary, f'risk_{i}', risk)

        db.add(summary)
        action = "创建"

    db.commit()
    print(f"✓ {action}完成")


def main():
    """主函数"""
    print("=" * 60)
    print("磐泽扬帆精选6号 数据导入工具")
    print("=" * 60)

    try:
        # 获取数据库会话
        with db_manager.get_session() as db:
            # 导入行业配置数据
            import_sector_allocation_data(db)

            # 导入分析摘要
            import_analysis_summary(db)

        print("\n" + "=" * 60)
        print("✓ 所有数据导入成功！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
