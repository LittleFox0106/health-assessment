"""
数据库配置与连接管理
支持 SQLite（本地开发）和 PostgreSQL（Supabase 生产环境）
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 数据库 URL 配置
# 本地开发使用 SQLite，生产环境通过 DATABASE_URL 环境变量切换为 PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./health_assessment.db"
)

# SQLite 需要启用 check_same_thread=False
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表结构"""
    Base.metadata.create_all(bind=engine)
