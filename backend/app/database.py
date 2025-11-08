"""
数据库配置和连接管理
Private Fund Management System Database Configuration
"""

import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from .models import Base, TABLES_CREATION_ORDER

# 配置日志
logger = logging.getLogger(__name__)

# 数据库配置
class DatabaseConfig:
    """数据库配置类"""
    
    # 开发环境 - SQLite
    SQLITE_DEV_URL = "sqlite:///./privatefund_dev.db"
    
    # Docker环境 - SQLite
    SQLITE_DOCKER_URL = "sqlite:////app/backend/app/privatefund_dev.db"
    
    # 生产环境 - MySQL
    MYSQL_PROD_URL = "mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    
    @classmethod
    def get_database_url(cls) -> str:
        """
        根据环境变量获取数据库连接URL
        """
        env = os.getenv("ENVIRONMENT", "development")
        
        if env == "production":
            # 生产环境使用MySQL
            mysql_config = {
                "user": os.getenv("DB_USER", "privatefund"),
                "password": os.getenv("DB_PASSWORD", "password"),
                "host": os.getenv("DB_HOST", "localhost"),
                "port": os.getenv("DB_PORT", "3306"),
                "database": os.getenv("DB_DATABASE", "privatefund")
            }
            return cls.MYSQL_PROD_URL.format(**mysql_config)
        elif env == "docker" or os.path.exists("/app/backend/app/privatefund_dev.db"):
            # Docker环境或Railway部署环境，使用预置的真实数据库
            return cls.SQLITE_DOCKER_URL
        else:
            # 开发环境使用SQLite
            return cls.SQLITE_DEV_URL


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.database_url = DatabaseConfig.get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
    
    def _setup_engine(self):
        """设置数据库引擎"""
        if "sqlite" in self.database_url:
            # SQLite配置
            self.engine = create_engine(
                self.database_url,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                poolclass=StaticPool,
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
        else:
            # MySQL配置
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"数据库引擎已初始化: {self.database_url}")
    
    def create_tables(self):
        """
        创建所有数据表
        按照依赖关系顺序创建，避免外键约束错误
        """
        try:
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
            
            # 记录创建的表
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            logger.info(f"已创建表: {', '.join(table_names)}")
            
        except Exception as e:
            logger.error(f"创建数据库表失败: {str(e)}")
            raise
    
    def drop_tables(self):
        """删除所有数据表（谨慎使用）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("所有数据库表已删除")
        except Exception as e:
            logger.error(f"删除数据库表失败: {str(e)}")
            raise
    
    def reset_database(self):
        """重置数据库（删除并重新创建所有表）"""
        logger.warning("正在重置数据库...")
        self.drop_tables()
        self.create_tables()
        logger.info("数据库重置完成")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话的上下文管理器
        自动处理提交和回滚
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话异常: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """直接获取数据库会话（需要手动管理）"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                logger.info("数据库连接测试成功")
                return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {str(e)}")
            return False
    
    def get_database_info(self) -> dict:
        """获取数据库信息"""
        try:
            with self.engine.connect() as connection:
                if "sqlite" in self.database_url:
                    # SQLite信息
                    result = connection.execute(text("PRAGMA database_list"))
                    db_info = result.fetchall()
                    return {
                        "type": "SQLite",
                        "url": self.database_url,
                        "info": db_info
                    }
                else:
                    # MySQL信息
                    result = connection.execute(text("SELECT VERSION()"))
                    version = result.fetchone()[0]
                    return {
                        "type": "MySQL",
                        "url": self.database_url.split("@")[1] if "@" in self.database_url else "N/A",
                        "version": version
                    }
        except Exception as e:
            logger.error(f"获取数据库信息失败: {str(e)}")
            return {"error": str(e)}


# 全局数据库管理器实例
db_manager = DatabaseManager()

# 便捷函数
def get_db() -> Generator[Session, None, None]:
    """FastAPI依赖注入使用的数据库会话获取函数"""
    with db_manager.get_session() as session:
        yield session

def init_database():
    """初始化数据库"""
    logger.info("正在初始化数据库...")
    
    # 测试连接
    if not db_manager.test_connection():
        raise Exception("数据库连接失败")
    
    # 创建表
    db_manager.create_tables()
    
    logger.info("数据库初始化完成")

def get_database_status() -> dict:
    """获取数据库状态信息"""
    return {
        "connection": db_manager.test_connection(),
        "info": db_manager.get_database_info(),
        "url": db_manager.database_url
    }