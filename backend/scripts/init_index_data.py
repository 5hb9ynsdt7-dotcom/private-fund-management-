"""
指数数据初始化脚本
用于批量导入历史指数数据到本地数据库

使用方法：
cd /Users/sudan/Desktop/Private\ Fund/privatefund/backend
./backend_venv/bin/python scripts/init_index_data.py
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import db_manager
from app.services.tushare_service import TushareIndexService, SUPPORTED_INDICES

def init_single_index(ts_code: str, index_name: str, start_date: str = '20150101'):
    """
    初始化单个指数的历史数据

    Args:
        ts_code: 指数代码，如 '000001.SH'
        index_name: 指数名称，如 '上证指数'
        start_date: 起始日期，默认从2015年开始（与净值数据对齐）
    """
    print(f"\n{'='*60}")
    print(f"开始初始化: {ts_code} - {index_name}")
    print(f"起始日期: {start_date}")
    print(f"{'='*60}")

    with db_manager.get_session() as db:
        service = TushareIndexService(db)
        result = service.initialize_index(ts_code, index_name, start_date)

        print(f"\n结果: {result['status']}")
        print(f"消息: {result['message']}")
        if 'inserted_count' in result:
            print(f"插入记录数: {result['inserted_count']}")
        if 'latest_date' in result:
            print(f"最新日期: {result['latest_date']}")

    print(f"{'='*60}\n")

def init_all_indices(start_date: str = '20150101'):
    """
    初始化所有支持的指数

    Args:
        start_date: 起始日期，默认从2015年开始（与净值数据对齐）
    """
    print("\n" + "="*80)
    print("指数数据批量初始化")
    print(f"支持的指数: {len(SUPPORTED_INDICES)} 个")
    print(f"起始日期: {start_date}")
    print("="*80)

    for ts_code, index_name in SUPPORTED_INDICES.items():
        try:
            init_single_index(ts_code, index_name, start_date)
        except Exception as e:
            print(f"❌ 初始化 {ts_code} 失败: {e}")
            continue

    print("\n" + "="*80)
    print("所有指数初始化完成")
    print("="*80 + "\n")

def update_all_indices():
    """
    增量更新所有已初始化的指数
    """
    print("\n" + "="*80)
    print("指数数据增量更新")
    print("="*80 + "\n")

    with db_manager.get_session() as db:
        service = TushareIndexService(db)

        for ts_code, index_name in SUPPORTED_INDICES.items():
            print(f"\n更新 {ts_code} - {index_name}")
            print("-" * 60)

            try:
                result = service.update_index_incremental(ts_code)
                print(f"状态: {result['status']}")
                print(f"消息: {result['message']}")
                if 'inserted_count' in result:
                    print(f"新增记录: {result['inserted_count']}")
            except Exception as e:
                print(f"❌ 更新失败: {e}")
                continue

    print("\n" + "="*80)
    print("所有指数更新完成")
    print("="*80 + "\n")

def show_status():
    """
    显示所有指数的状态
    """
    print("\n" + "="*80)
    print("指数数据状态")
    print("="*80 + "\n")

    with db_manager.get_session() as db:
        service = TushareIndexService(db)
        statuses = service.get_all_indices_status()

        if not statuses:
            print("暂无指数数据")
        else:
            for status in statuses:
                print(f"{status['ts_code']} - {status['index_name']}")
                print(f"  最新日期: {status['latest_trade_date']}")
                print(f"  总记录数: {status['total_records']}")
                print(f"  最后更新: {status['last_update_time']}")
                print(f"  是否激活: {status['is_active']}")
                print()

    print("="*80 + "\n")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='指数数据管理脚本')
    parser.add_argument(
        'action',
        choices=['init', 'init-all', 'update', 'status', 'init-sh'],
        help='''
        init: 初始化指定指数
        init-all: 初始化所有指数
        update: 增量更新所有指数
        status: 查看所有指数状态
        init-sh: 仅初始化上证指数(000001.SH)
        '''
    )
    parser.add_argument(
        '--code',
        type=str,
        help='指数代码（用于init操作），如 000001.SH'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='指数名称（用于init操作），如 上证指数'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='20150101',
        help='起始日期，格式YYYYMMDD，默认20150101'
    )

    args = parser.parse_args()

    if args.action == 'init':
        if not args.code or not args.name:
            print("❌ init操作需要指定 --code 和 --name 参数")
            sys.exit(1)
        init_single_index(args.code, args.name, args.start_date)

    elif args.action == 'init-all':
        init_all_indices(args.start_date)

    elif args.action == 'update':
        update_all_indices()

    elif args.action == 'status':
        show_status()

    elif args.action == 'init-sh':
        # 仅初始化上证指数
        init_single_index('000001.SH', '上证指数', args.start_date)
