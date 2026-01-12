#!/usr/bin/env python3
"""
创建项目持仓分析相关数据库表
Create Project Holding Analysis Database Tables
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine
from app.models import Base, ProjectHoldingAsset, ProjectHoldingIndustry
from app.database import get_database_url

def create_project_holding_tables():
    """
    创建项目持仓分析相关的数据库表
    """
    try:
        # 获取数据库URL
        database_url = get_database_url()
        print(f"数据库连接: {database_url}")
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 只创建项目持仓相关的表
        tables_to_create = [
            ProjectHoldingAsset.__table__,
            ProjectHoldingIndustry.__table__
        ]
        
        # 创建表
        print("开始创建项目持仓分析相关表...")
        
        for table in tables_to_create:
            try:
                table.create(engine, checkfirst=True)
                print(f"✓ 成功创建表: {table.name}")
            except Exception as e:
                print(f"✗ 创建表 {table.name} 失败: {str(e)}")
        
        print("\n项目持仓分析表创建完成!")
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print("\n验证表创建结果:")
        for table in ['project_holding_asset', 'project_holding_industry']:
            if table in existing_tables:
                print(f"✓ {table} - 已创建")
                
                # 显示表结构
                columns = inspector.get_columns(table)
                print(f"  字段数量: {len(columns)}")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
                print()
            else:
                print(f"✗ {table} - 未找到")
        
    except Exception as e:
        print(f"创建表失败: {str(e)}")
        sys.exit(1)

def main():
    """
    主函数
    """
    print("=" * 60)
    print("项目持仓分析 - 数据库表创建工具")
    print("=" * 60)
    
    create_project_holding_tables()
    
    print("=" * 60)
    print("操作完成!")

if __name__ == "__main__":
    main()