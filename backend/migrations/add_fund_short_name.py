"""
添加基金简称字段并自动生成简称
执行方式：python migrations/add_fund_short_name.py
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database import DatabaseConfig
from app.models import Fund


def add_short_name_column():
    """添加short_name字段到fund表"""
    engine = create_engine(DatabaseConfig.get_database_url())

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('fund')
            WHERE name = 'short_name'
        """))

        count = result.fetchone()[0]

        if count > 0:
            print("✓ short_name 字段已存在")
        else:
            print("正在添加 short_name 字段...")
            conn.execute(text("""
                ALTER TABLE fund
                ADD COLUMN short_name VARCHAR(100)
            """))
            conn.commit()
            print("✓ short_name 字段添加成功")


def generate_all_short_names():
    """为所有基金生成简称"""
    engine = create_engine(DatabaseConfig.get_database_url())

    with engine.connect() as conn:
        # 获取所有基金
        result = conn.execute(text("SELECT fund_code, fund_name FROM fund"))
        funds = result.fetchall()

        print(f"\n开始为 {len(funds)} 个基金生成简称...")

        updated_count = 0
        for fund in funds:
            fund_code = fund[0]
            fund_name = fund[1]

            # 生成简称
            short_name = Fund.generate_short_name(fund_name)

            # 更新数据库
            conn.execute(
                text("UPDATE fund SET short_name = :short_name WHERE fund_code = :fund_code"),
                {"short_name": short_name, "fund_code": fund_code}
            )

            print(f"  {fund_code}: {fund_name} -> {short_name}")
            updated_count += 1

        conn.commit()
        print(f"\n✓ 成功更新 {updated_count} 个基金的简称")


if __name__ == "__main__":
    print("=" * 60)
    print("基金简称字段迁移脚本")
    print("=" * 60)

    try:
        # 步骤1：添加字段
        add_short_name_column()

        # 步骤2：生成简称
        generate_all_short_names()

        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
