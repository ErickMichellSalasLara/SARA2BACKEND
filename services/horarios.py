# Horarios de salones
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Esquema para cuando el administrador quiera cambiar el horario
class ActualizarHorario(BaseModel):
    dia: str
    apertura: str
    cierre: str
    cerrado: bool

# Datos simulados en memoria (hasta que se conecte SQLite)
horarios_semana = [
    {"id": 1, "dia": "Lunes", "apertura": "07:30", "cierre": "20:00", "cerrado": False},
    {"id": 2, "dia": "Martes", "apertura": "07:30", "cierre": "20:00", "cerrado": False},
    {"id": 3, "dia": "Miércoles", "apertura": "07:30", "cierre": "20:00", "cerrado": False},
    {"id": 4, "dia": "Jueves", "apertura": "07:30", "cierre": "20:00", "cerrado": False},
    {"id": 5, "dia": "Viernes", "apertura": "07:30", "cierre": "20:00", "cerrado": False},
    {"id": 6, "dia": "Sábado", "apertura": "09:00", "cierre": "13:00", "cerrado": False},
    {"id": 7, "dia": "Domingo", "apertura": "-", "cierre": "-", "cerrado": True},
]

@router.get("/")
def obtener_horarios():
    return {"horarios": horarios_semana}

@router.put("/{dia_id}")
def actualizar_horario(dia_id: int, horario: ActualizarHorario):
    for h in horarios_semana:
        if h["id"] == dia_id:
            h["apertura"] = horario.apertura
            h["cierre"] = horario.cierre
            h["cerrado"] = horario.cerrado
            return {"mensaje": "Horario actualizado correctamente", "horario": h}

    raise HTTPException(status_code=404, detail="Día no encontrado")