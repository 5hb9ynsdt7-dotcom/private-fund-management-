"""
更新会世元丰2号(L03092)的分析摘要数据
"""
from datetime import datetime
from app.database import db_manager
from app.models_product_analysis import ProductAnalysisSummary

def update_summary():
    with db_manager.get_session() as db:
        # 查找或创建记录
        summary = db.query(ProductAnalysisSummary).filter(
            ProductAnalysisSummary.product_code == "L03092"
        ).first()

        if summary:
            # 更新分析区间
            summary.analysis_start_date = datetime.strptime("2025-08-01", "%Y-%m-%d").date()
            summary.analysis_end_date = datetime.strptime("2026-01-31", "%Y-%m-%d").date()
            db.commit()
            print("✓ 已更新会世元丰2号分析区间: 2025-08 至 2026-01")
        else:
            print("✗ 未找到L03092的分析摘要记录")

if __name__ == "__main__":
    update_summary()
