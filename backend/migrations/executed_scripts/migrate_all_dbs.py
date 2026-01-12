"""
为所有数据库文件添加 pre_dividend_nav 字段
Migrate all database files to add pre_dividend_nav column
"""

import sqlite3
from pathlib import Path

# 查找所有数据库文件
DB_FILES = [
    Path(__file__).parent / "privatefund_dev.db",
    Path(__file__).parent / "app" / "privatefund_dev.db",
]

def migrate_database(db_path: Path):
    """为单个数据库添加列"""
    if not db_path.exists():
        print(f"⊗ 跳过: {db_path} (文件不存在)")
        return False

    print(f"\n处理数据库: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(dividend)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'pre_dividend_nav' in columns:
            print("  ✓ pre_dividend_nav 列已存在，无需迁移")
            return True

        # 添加新列
        cursor.execute("""
            ALTER TABLE dividend
            ADD COLUMN pre_dividend_nav DECIMAL(16, 4)
        """)

        conn.commit()
        print("  ✓ 成功添加 pre_dividend_nav 列")

        # 验证
        cursor.execute("PRAGMA table_info(dividend)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'pre_dividend_nav' in columns:
            print("  ✓ 验证成功")
            return True
        else:
            print("  ✗ 验证失败")
            return False

    except Exception as e:
        conn.rollback()
        print(f"  ✗ 迁移失败: {e}")
        return False
    finally:
        conn.close()

def main():
    print("=" * 70)
    print("数据库迁移: 添加 pre_dividend_nav 字段到所有数据库")
    print("=" * 70)

    success_count = 0
    total_count = 0

    for db_path in DB_FILES:
        total_count += 1
        if migrate_database(db_path):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"迁移完成: {success_count}/{total_count} 个数据库成功")
    print("=" * 70)

if __name__ == "__main__":
    main()
