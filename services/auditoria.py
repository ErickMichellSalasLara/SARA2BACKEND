from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class AuditoriaCreate(BaseModel):
    admin: str
    action: str
    module: str
    record: str
    date: str

# --- SIMULADOR DE BASE DE DATOS ---
# Empezamos con unos registros de prueba para que tu tabla no esté vacía
base_de_datos_auditoria = [
    {
        "id": 1,
        "admin": "Sistema S.A.R.A.",
        "action": "Inicialización del sistema",
        "module": "Configuración",
        "record": "Arranque",
        "date": "2026-08-01 08:00",
        "ip": "127.0.0.1",
    }
]
contador_id = 2

@router.get("/historial")
async def obtener_historial():
    try:
        # Devolvemos la lista invertida para que los eventos recientes salgan primero
        return {"auditoria": list(reversed(base_de_datos_auditoria))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/registrar")
async def registrar_auditoria(auditoria: AuditoriaCreate):
    global contador_id
    try:
        nuevo_registro = {
            "id": contador_id,
            "admin": auditoria.admin,
            "action": auditoria.action,
            "module": auditoria.module,
            "record": auditoria.record,
            # Formateamos la hora actual para que se vea bien en tu tabla
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ip": "127.0.0.1" # En el futuro, aquí puedes capturar la IP real del request
        }

        # Lo guardamos en nuestra "base de datos"
        base_de_datos_auditoria.append(nuevo_registro)
        contador_id += 1

        print(f"✅ Guardado en tabla: {auditoria.admin} -> {auditoria.action}")
        return {"mensaje": "Registro exitoso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))