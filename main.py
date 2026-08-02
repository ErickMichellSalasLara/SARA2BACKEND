from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. Inicializar la aplicación
app = FastAPI(title="S.A.R.A. Backend")

# 2. Configurar CORS para permitir que React (Frontend) se comunique
# Ajusta el puerto 3000 si tu React corre en otro distinto
origenes_permitidos = [
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Permite todos los headers
)

# --- MODELOS DE DATOS (PYDANTIC) ---
# Esto define la estructura exacta que esperamos recibir de Reactl. PYDANTIC valida los json recibidos
class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False

# --- ENDPOINTS ---
@app.get("/")
def ruta_principal():
    return {"mensaje": "¡Bienvenido a la API de S.A.R.A!"}

# Nuevo endpoint de Login
@app.post("/api/auth/login")
def login(request: LoginRequest):
    # SIMULACIÓN DE BASE DE DATOS:
    # Por ahora hardcodeamos un usuario administrador válido para probar
    if request.email == "admin@utr.edu.mx" and request.password == "admin12345":
        # Respuesta exitosa que espera tu React
        return {
            "token": "token_simulado_12345_sara",
            "user": {
                "name": "Administrador Principal"
            }
        }

    # Si las credenciales no coinciden, lanzamos un error 401 (No autorizado)
    # Tu bloque catch en React capturará el "detail"
    raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")