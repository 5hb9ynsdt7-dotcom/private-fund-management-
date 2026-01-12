#!/usr/bin/env python3
"""
更新L03125基金名称的脚本
Update L03125 Fund Name Script
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import db_manager
from app.models import Fund

def update_fund_name():
    """更新L03125基金的正确名称"""
    with db_manager.get_session() as session:
        # 查找L03125基金
        fund = session.query(Fund).filter(Fund.fund_code == 'L03125').first()
        
        if fund:
            print(f"找到基金：{fund.fund_code}")
            print(f"当前名称：{fund.fund_name}")
            
            # 更新为正确的基金名称
            new_name = "龙舟-会世趋势CTA1号私募证券投资基金"
            fund.fund_name = new_name
            
            print(f"已更新为：{new_name}")
            print("✅ 基金名称更新成功!")
            
        else:
            print("❌ 未找到L03125基金")

def check_all_funds():
    """检查所有基金的名称，找出可能需要更新的基金"""
    with db_manager.get_session() as session:
        funds = session.query(Fund).all()
        print("📋 所有基金列表：")
        print("-" * 60)
        
        for fund in funds:
            status = "⚠️  需要更新" if fund.fund_name.startswith("基金_") else "✅ 名称正常"
            print(f"{fund.fund_code:<10} | {fund.fund_name:<30} | {status}")

if __name__ == "__main__":
    print("🔍 检查所有基金名称...")
    check_all_funds()
    
    print("\n" + "="*60)
    print("🔧 开始更新L03125基金名称...")
    update_fund_name()
    
    print("\n🔍 更新后再次检查...")
    check_all_funds()