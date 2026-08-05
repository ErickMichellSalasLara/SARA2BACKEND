import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Magia de entorno: Usa la BD local en tu PC, pero usará la de Railway en la nube
URL_BASE_DATOS = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:MLRKGSdQsngwHusQylWxpqYzYDiksbXm@altaria.proxy.rlwy.net:21920/railway"
)

engine = create_engine(URL_BASE_DATOS)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Esta función es la que usarán TODOS tus archivos para pedir datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()