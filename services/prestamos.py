# Libros
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Esquema para recibir los datos desde el frontend
class SolicitudPrestamo(BaseModel):
    matricula: str
    material: str

# Datos simulados (mock data)
registro_prestamos = [
    {"id": 1, "matricula": "210345", "nombre": "Laura Martínez", "material": "Libro 1", "hora_prestamo": "08:15", "hora_devolucion": None, "estatus": "Activo"},
    {"id": 2, "matricula": "220112", "nombre": "Sofía Castro", "material": "Libro 2", "hora_prestamo": "10:00", "hora_devolucion": "11:00", "estatus": "Devuelto"},
]

@router.get("/historial")
def obtener_prestamos():
    return {"prestamos": registro_prestamos}

@router.post("/registrar")
def registrar_prestamo(datos: SolicitudPrestamo):
    nuevo_prestamo = {
        "id": len(registro_prestamos) + 1,
        "matricula": datos.matricula,
        "nombre": "Estudiante Prueba", # Esto lo sacaremos de SQLite después
        "material": datos.material,
        "hora_prestamo": datetime.now().strftime("%H:%M"),
        "hora_devolucion": None,
        "estatus": "Activo"
    }
    registro_prestamos.append(nuevo_prestamo)
    return {"mensaje": f"Préstamo de '{datos.material}' registrado exitosamente", "datos": nuevo_prestamo}

@router.put("/devolver/{prestamo_id}")
def devolver_prestamo(prestamo_id: int):
    # Buscamos el préstamo por su ID para registrar la devolución
    for prestamo in registro_prestamos:
        if prestamo["id"] == prestamo_id and prestamo["estatus"] == "Activo":
            prestamo["hora_devolucion"] = datetime.now().strftime("%H:%M")
            prestamo["estatus"] = "Devuelto"
            return {"mensaje": "Material devuelto correctamente", "datos": prestamo}

    return {"mensaje": "Préstamo no encontrado o ya devuelto"}