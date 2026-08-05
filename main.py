from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.prestamos import router as prestamos_router
from services.auditoria import router as auditoria_router

# --- IMPORTACIONES MÁGICAS (Solución al NameError) ---
from services.reportes import router as reportes_router
from services.reservas import router as reservas_router
from services.acceso import router as acceso_router

app = FastAPI(title="S.A.R.A. Backend")

origenes_permitidos = [
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "https://sara2-production.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False

# --- CONEXIÓN DE LOS MÓDULOS ---
app.include_router(reportes_router, prefix="/api/reportes", tags=["Reportes"])
app.include_router(reservas_router, prefix="/api/calendario", tags=["Calendario"])
app.include_router(acceso_router, prefix="/api/accesos", tags=["Accesos"])
app.include_router(prestamos_router, prefix="/api/prestamos", tags=["Prestamos"])
app.include_router(auditoria_router, prefix="/api/auditoria", tags=["Auditoria"])

@app.get("/")
def ruta_principal():
    return {"mensaje": "¡Bienvenido a la API de S.A.R.A!"}

@app.post("/api/auth/login")
def login(request: LoginRequest):
    if request.email == "admin@utr.edu.mx" and request.password == "admin12345":
        return {
            "token": "token_simulado_12345_sara",
            "user": {"name": "Administrador Principal", "role": "admin"}
        }
    raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")