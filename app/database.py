from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from . import config

# SQLite 需要允许跨线程访问（后台任务与请求线程共用引擎）
connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping：云平台会主动断开空闲连接，取连接前先探活，避免 "server closed the connection"
engine = create_engine(config.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖：请求级数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
