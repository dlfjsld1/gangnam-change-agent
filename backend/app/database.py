import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gangnam-change-agent.db")
_engine_options: dict[str, object] = {"pool_pre_ping": True}
if DATABASE_URL == "sqlite+pysqlite:///:memory:":
    _engine_options.update(
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
