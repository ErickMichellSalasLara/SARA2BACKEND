from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from core.config import APP_NAME, CORS_ORIGINS
from database import engine
from routers import (
    accesses,
    audit,
    auth,
    cubicles,
    dashboard,
    loans,
    reports,
    reservations,
    settings,
    users,
)

app = FastAPI(
    title=APP_NAME,
    version="2.0.0",
    description="API de S.A.R.A. para autenticación, cubículos, reservas y administración.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(cubicles.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(reservations.router, prefix="/api/calendario")
app.include_router(reservations.calendar_router, prefix="/api")
app.include_router(accesses.router, prefix="/api")
app.include_router(loans.router, prefix="/api/prestamos")
app.include_router(users.router, prefix="/api")
app.include_router(audit.router, prefix="/api/auditoria")
app.include_router(settings.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "API de S.A.R.A. disponible.",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/mensaje")
def message():
    return {"mensaje": "Conexión correcta entre React y FastAPI."}


@app.get("/api/health")
def health():
    return {"status": "ok", "service": APP_NAME}


@app.get("/api/health/database")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
