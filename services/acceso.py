# Control de acceso RFID
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class RegistroAcceso(BaseModel):
    matricula: str

# Datos simulados de las visitas de hoy
registro_accesos = [
    {"id": 1, "matricula": "210345", "nombre": "Laura Martínez", "hora_entrada": "08:15", "hora_salida": "10:30", "estatus": "Completado"},
    {"id": 2, "matricula": "210899", "nombre": "Diego Fernández", "hora_entrada": "09:00", "hora_salida": None, "estatus": "En sitio"},
    {"id": 3, "matricula": "220112", "nombre": "Sofía Castro", "hora_entrada": "11:20", "hora_salida": None, "estatus": "En sitio"},
]

@router.get("/historial")
def obtener_historial_accesos():
    return {"accesos": registro_accesos}

@router.post("/registrar")
def registrar_entrada_salida(datos: RegistroAcceso):
    hora_actual = datetime.now().strftime("%H:%M")

    # Buscamos si el alumno ya está "En sitio" para registrar su salida
    for acceso in registro_accesos:
        if acceso["matricula"] == datos.matricula and acceso["estatus"] == "En sitio":
            acceso["hora_salida"] = hora_actual
            acceso["estatus"] = "Completado"
            return {"mensaje": "Salida registrada correctamente", "datos": acceso}

    # Si no estaba adentro, registramos una nueva entrada
    nuevo_registro = {
        "id": len(registro_accesos) + 1,
        "matricula": datos.matricula,
        "nombre": "Estudiante Prueba",  # Esto se buscará en SQLite después
        "hora_entrada": hora_actual,
        "hora_salida": None,
        "estatus": "En sitio"
    }
    registro_accesos.append(nuevo_registro)

    return {"mensaje": "Entrada registrada exitosamente", "datos": nuevo_registro}