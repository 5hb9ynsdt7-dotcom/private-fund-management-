"""创建产品清单表"""
from sqlalchemy import create_engine
from app.models import Base, ProductList, ProductListItem
from app.database import DatabaseConfig

# 获取数据库URL并创建引擎
database_url = DatabaseConfig.get_database_url()
engine = create_engine(database_url)

# 创建表
ProductList.__table__.create(engine, checkfirst=True)
ProductListItem.__table__.create(engine, checkfirst=True)

print("产品清单表创建成功！")
