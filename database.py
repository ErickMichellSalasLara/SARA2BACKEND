import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import DATABASE_TIMEZONE


def _normalize_database_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if raw_url.startswith("mysql://"):
        return raw_url.replace("mysql://", "mysql+pymysql://", 1)
    return raw_url


raw_database_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("MYSQL_URL")
    or "mysql+pymysql://root:@127.0.0.1:3306/sara_db"
)
DATABASE_URL = _normalize_database_url(raw_database_url)
database_url = make_url(DATABASE_URL)

engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
    "future": True,
}

if database_url.drivername.startswith("mysql"):
    engine_options["connect_args"] = {
        "charset": "utf8mb4",
        "init_command": f"SET time_zone = '{DATABASE_TIMEZONE}'",
    }

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
