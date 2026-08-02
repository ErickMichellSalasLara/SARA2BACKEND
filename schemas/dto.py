# Nuevo endpoint de Login
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False

@app.post("/api/auth/login")
def login(request: LoginRequest):
    # SIMULACIÓN DE BASE DE DATOS:
    # Por ahora hardcodeamos un usuario administrador válido para probar
    if request.email == "admin@utr.edu.mx" and request.password == "admin12345":
        # Respuesta exitosa que espera tu React
        return {
            "token": "token_simulado_12345_sara",
            "user": {
                "name": "Administrador Principal",
                "role": "admin"
            }
        }

    # Si las credenciales no coinciden, lanzamos un error 401 (No autorizado)
    # Tu bloque catch en React capturará el "detail"
    raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")