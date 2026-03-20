"""
数据库迁移脚本：添加组合净值表 (portfolio_nav)
创建日期：2026-03-19
用途：支持回测组合和实盘组合的净值存储，用于业绩PK对比
"""
import sqlite3
import os
from datetime import datetime

def migrate(db_path: str):
    """执行数据库迁移"""
    print(f"开始迁移: 添加 portfolio_nav 表")
    print(f"数据库路径: {db_path}")

    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='portfolio_nav'
        """)

        if cursor.fetchone():
            print("表 portfolio_nav 已存在，跳过创建")
            return True

        # 创建 portfolio_nav 表
        cursor.execute("""
            CREATE TABLE portfolio_nav (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_type VARCHAR(20) NOT NULL,
                portfolio_id INTEGER NOT NULL,
                portfolio_name VARCHAR(100),
                nav_date DATE NOT NULL,
                unit_nav DECIMAL(16, 6) NOT NULL,
                accum_nav DECIMAL(16, 6) NOT NULL,
                daily_return DECIMAL(12, 6),
                total_return DECIMAL(12, 4),
                total_value DECIMAL(20, 2),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建唯一约束索引
        cursor.execute("""
            CREATE UNIQUE INDEX uix_portfolio_nav
            ON portfolio_nav(portfolio_type, portfolio_id, nav_date)
        """)

        # 创建查询优化索引
        cursor.execute("""
            CREATE INDEX idx_portfolio_nav_lookup
            ON portfolio_nav(portfolio_type, portfolio_id, nav_date)
        """)

        # 创建日期索引
        cursor.execute("""
            CREATE INDEX idx_portfolio_nav_date
            ON portfolio_nav(nav_date)
        """)

        conn.commit()
        print("✓ 成功创建 portfolio_nav 表及索引")

        # 验证表结构
        cursor.execute("PRAGMA table_info(portfolio_nav)")
        columns = cursor.fetchall()
        print(f"✓ 表结构验证通过，共 {len(columns)} 个字段")

        return True

    except Exception as e:
        print(f"✗ 迁移失败: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()


def rollback(db_path: str):
    """回滚迁移"""
    print(f"开始回滚: 删除 portfolio_nav 表")

    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS portfolio_nav")
        conn.commit()
        print("✓ 成功删除 portfolio_nav 表")
        return True

    except Exception as e:
        print(f"✗ 回滚失败: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    # 默认数据库路径
    default_db = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "privatefund_dev.db"
    )

    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db

    # 执行迁移
    print("=" * 60)
    print("组合净值表迁移脚本")
    print("=" * 60)

    if migrate(db_path):
        print("\n迁移成功完成！")

        # 记录迁移历史
        script_name = os.path.basename(__file__)
        executed_dir = os.path.join(os.path.dirname(__file__), "executed_scripts")
        os.makedirs(executed_dir, exist_ok=True)

        record_file = os.path.join(executed_dir, f"{script_name}.executed")
        with open(record_file, 'w') as f:
            f.write(f"Executed at: {datetime.now().isoformat()}\n")
            f.write(f"Database: {db_path}\n")

        print(f"迁移记录已保存: {record_file}")
    else:
        print("\n迁移失败！")
        sys.exit(1)
