"""
导出国源拾金2号图表到Obsidian
"""
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import pandas as pd
from datetime import datetime
from app.database import db_manager
from app.models import Nav
from app.models_product_analysis import ProductSectorAllocation
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = "/Users/sudan/Desktop/ObsidianVault/研究笔记/私募产品研究/国源拾金2号"

def export_nav_chart():
    """导出净值走势与回撤图"""
    with db_manager.get_session() as db:
        nav_records = db.query(Nav).filter(
            Nav.fund_code == "L03143",
            Nav.nav_date >= datetime(2025, 10, 1).date()
        ).order_by(Nav.nav_date).all()

        if not nav_records:
            print("无净值数据")
            return

        dates = [r.nav_date for r in nav_records]
        navs = [float(r.unit_nav) for r in nav_records]

        # 计算回撤
        peak = navs[0]
        drawdowns = []
        for nav in navs:
            if nav > peak:
                peak = nav
            dd = ((nav - peak) / peak) * 100
            drawdowns.append(dd)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # 净值曲线
        ax1.plot(dates, navs, color='#409EFF', linewidth=2)
        ax1.set_ylabel('净值', fontsize=12)
        ax1.set_title('国源拾金2号 净值走势与回撤', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # 回撤曲线
        ax2.fill_between(dates, drawdowns, 0, color='#67C23A', alpha=0.3)
        ax2.plot(dates, drawdowns, color='#67C23A', linewidth=2)
        ax2.set_ylabel('回撤(%)', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/净值走势与回撤.png", dpi=150, bbox_inches='tight')
        plt.close()
        print("✓ 净值走势与回撤图已保存")

def export_sector_chart():
    """导出行业配置多空结构图"""
    with db_manager.get_session() as db:
        allocations = db.query(ProductSectorAllocation).filter(
            ProductSectorAllocation.product_code == "L03143"
        ).order_by(ProductSectorAllocation.allocation_date).all()

        if not allocations:
            print("无行业配置数据")
            return

        # 按月份组织数据
        months_data = {}
        for alloc in allocations:
            month_key = alloc.allocation_date.strftime("%Y-%m")
            if month_key not in months_data:
                months_data[month_key] = {'long': {}, 'short': {}}

            if alloc.position_type.value == 'long':
                months_data[month_key]['long'][alloc.sector_name] = alloc.allocation_pct
            else:
                months_data[month_key]['short'][alloc.sector_name] = alloc.allocation_pct

        months = sorted(months_data.keys())
        month_labels = [m.split('-')[1] + '月' for m in months]

        # 收集所有行业
        all_sectors = set()
        for data in months_data.values():
            all_sectors.update(data['long'].keys())
            all_sectors.update(data['short'].keys())

        # 准备数据 - 分离现金和股票
        cash_data = []
        stock_long_data = {}
        stock_short_data = {}

        for month in months:
            cash_data.append(months_data[month]['long'].get('现金管理工具', 0))

            for sector in all_sectors:
                if sector == '现金管理工具':
                    continue
                if sector not in stock_long_data:
                    stock_long_data[sector] = []
                    stock_short_data[sector] = []
                stock_long_data[sector].append(months_data[month]['long'].get(sector, 0))
                # 空头数据已经在数据库中存储，不需要再取负
                short_val = months_data[month]['short'].get(sector, 0)
                stock_short_data[sector].append(-short_val if short_val > 0 else 0)

        # 绘图
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = {
            '现金管理工具': '#E8E8E8', '有色金属': '#DAA520', '汽车': '#FF6B6B',
            '电力设备': '#4ECDC4', '电子': '#556FB5', '家用电器': '#95E1D3',
            '基础化工': '#F38181', '期货-有色金属': '#DAA520', '社会服务': '#AA96DA',
            '其他': '#FCBAD3', '医药生物': '#A8E6CF', '电池': '#FFD93D',
            '房地产': '#FF6347', '科技': '#A29BFE', '非银金融': '#6BCB77',
            '农林牧渔': '#C7CEEA', '商贸零售': '#FFEAA7', '石油石化': '#74B9FF',
            '期货-化工': '#F38181'
        }

        x = np.arange(len(month_labels))

        # 先画现金（底部）
        ax.bar(x, cash_data, label='现金管理工具', color='#E8E8E8', width=0.6)
        bottom_long = np.array(cash_data, dtype=float)

        # 再画股票多头（堆叠在现金上方）
        for sector, vals in stock_long_data.items():
            vals_arr = np.array(vals, dtype=float)
            if any(v > 0 for v in vals_arr):
                ax.bar(x, vals_arr, bottom=bottom_long, label=sector,
                      color=colors.get(sector, '#5470C6'), width=0.6)
                bottom_long += vals_arr

        # 最后画期货空头（负值区域）
        bottom_short = np.zeros(len(months), dtype=float)
        for sector, vals in stock_short_data.items():
            vals_arr = np.array(vals, dtype=float)
            if any(v < 0 for v in vals_arr):
                ax.bar(x, vals_arr, bottom=bottom_short, label=sector+'(空)',
                      color=colors.get(sector, '#5470C6'), alpha=0.6, width=0.6, hatch='//')
                bottom_short += vals_arr

        ax.set_xticks(x)
        ax.set_xticklabels(month_labels)
        ax.set_ylabel('配置比例(%)', fontsize=12)
        ax.set_title('国源拾金2号 行业配置多空结构 (2025年10月-2026年2月)', fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.axhline(y=0, color='black', linewidth=0.8)

        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/行业配置多空结构.png", dpi=150, bbox_inches='tight')
        plt.close()
        print("✓ 行业配置多空结构图已保存")

def export_monthly_return_chart():
    """导出月度收益分布图"""
    with db_manager.get_session() as db:
        nav_records = db.query(Nav).filter(
            Nav.fund_code == "L03143",
            Nav.nav_date >= datetime(2025, 10, 1).date()
        ).order_by(Nav.nav_date).all()

        if not nav_records:
            print("无净值数据")
            return

        # 计算月度收益
        monthly_returns = []
        monthly_labels = []

        data = [(r.nav_date, float(r.unit_nav)) for r in nav_records]
        months = {}
        for date, nav in data:
            month_key = date.strftime("%Y-%m")
            if month_key not in months:
                months[month_key] = []
            months[month_key].append((date, nav))

        sorted_months = sorted(months.keys())
        prev_nav = None

        for month in sorted_months:
            month_data = sorted(months[month])
            start_nav = month_data[0][1]
            end_nav = month_data[-1][1]

            if prev_nav:
                ret = ((start_nav - prev_nav) / prev_nav) * 100
            else:
                ret = 0

            monthly_returns.append(ret)
            monthly_labels.append(month.split('-')[1] + '月')
            prev_nav = end_nav

        # 绘图
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#F56C6C' if r >= 0 else '#67C23A' for r in monthly_returns]

        bars = ax.bar(monthly_labels, monthly_returns, color=colors, width=0.6)
        ax.set_ylabel('收益率(%)', fontsize=12)
        ax.set_title('国源拾金2号 月度收益分布', fontsize=14, fontweight='bold')
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.grid(True, alpha=0.3, axis='y')

        # 添加数值标签
        for bar, ret in zip(bars, monthly_returns):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{ret:+.2f}%', ha='center', va='bottom' if height > 0 else 'top',
                   fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/月度收益分布.png", dpi=150, bbox_inches='tight')
        plt.close()
        print("✓ 月度收益分布图已保存")

if __name__ == "__main__":
    export_nav_chart()
    export_sector_chart()
    export_monthly_return_chart()
    print("\n所有图表已导出到:", OUTPUT_DIR)
