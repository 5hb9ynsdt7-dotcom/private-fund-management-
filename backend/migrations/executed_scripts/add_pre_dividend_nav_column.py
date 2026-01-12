"""
添加 pre_dividend_nav 字段到 dividend 表的数据库迁移脚本
Database Migration: Add pre_dividend_nav column to dividend table
"""

import sqlite3
from pathlib import Path

# 数据库文件路径
DB_PATH = Path(__file__).parent / "app" / "privatefund_dev.db"

def migrate():
    """执行数据库迁移"""
    print(f"连接数据库: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"错误: 数据库文件不存在: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(dividend)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'pre_dividend_nav' in columns:
            print("✓ pre_dividend_nav 列已存在，无需迁移")
            return

        print("开始添加 pre_dividend_nav 列...")

        # 添加新列
        cursor.execute("""
            ALTER TABLE dividend
            ADD COLUMN pre_dividend_nav DECIMAL(16, 4)
        """)

        conn.commit()
        print("✓ 成功添加 pre_dividend_nav 列")

        # 验证
        cursor.execute("PRAGMA table_info(dividend)")
        columns = cursor.fetchall()
        print("\n当前 dividend 表结构:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")

    except Exception as e:
        conn.rollback()
        print(f"✗ 迁移失败: {e}")
        raise

    finally:
        conn.close()
        print("\n数据库连接已关闭")

if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移: 添加 pre_dividend_nav 字段")
    print("=" * 60)
    migrate()
    print("\n迁移完成!")
