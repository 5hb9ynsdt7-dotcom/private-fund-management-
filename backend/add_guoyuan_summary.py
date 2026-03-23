"""
添加国源恰金2号(L03143)深度分析摘要
"""
from datetime import datetime
from app.database import db_manager
from app.models_product_analysis import ProductAnalysisSummary

def add_summary():
    with db_manager.get_session() as db:
        # 删除旧数据
        db.query(ProductAnalysisSummary).filter(
            ProductAnalysisSummary.product_code == "L03143"
        ).delete()

        # 创建新摘要
        summary = ProductAnalysisSummary(
            product_code="L03143",
            strategy_description="主观多头策略，基于基本面研究精选个股。2025年12月起大幅提升现金仓位至61.4%，2026年2月引入期货空头对冲，显示出灵活的风险管理能力。",
            highlight_1="长期业绩优秀：成立以来年化收益约24%，2025年全年收益54.41%",
            highlight_2="风险控制能力强：主动降低仓位、引入期货对冲工具",
            highlight_3="仓位管理灵活：根据市场环境调整股票/现金/期货配置",
            highlight_4="回撤控制良好：通过灵活仓位管理控制回撤风险",
            risk_1="高现金仓位：长期维持50-60%现金，可能错失市场上涨机会",
            risk_2="期货对冲成本：空头对冲会降低上涨弹性，增加交易成本",
            risk_3="市场波动风险：2026年2月引入对冲后短期波动加大",
            analysis_start_date=datetime.strptime("2025-10-01", "%Y-%m-%d").date(),
            analysis_end_date=datetime.strptime("2026-02-28", "%Y-%m-%d").date()
        )

        db.add(summary)
        db.commit()
        print("✓ 成功添加L03143深度分析摘要")

if __name__ == "__main__":
    add_summary()
