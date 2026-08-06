from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from database import get_db

router = APIRouter()

class AuditCreate(BaseModel):
    actor_user_id: int
    action: str
    module: str
    record_label: str

# Insertar registro de auditoría
@router.post("/registrar")
def registrar_auditoria(audit: AuditCreate, db: Session = Depends(get_db)):
    query = text("""
                 INSERT INTO audit_logs (actor_user_id, action, module, record_label, occurred_at)
                 VALUES (:actor_user_id, :action, :module, :record_label, NOW())
                 """)
    db.execute(query, {
        "actor_user_id": audit.actor_user_id,
        "action": audit.action,
        "module": audit.module,
        "record_label": audit.record_label
    })
    db.commit()
    return {"mensaje": "Registro de auditoría guardado"}

# DELETE (Mantenimiento de logs antiguos)
@router.delete("/limpiar")
def limpiar_auditoria(fecha_limite: str = "2026-01-01", db: Session = Depends(get_db)):
    query = text("DELETE FROM audit_logs WHERE occurred_at < :fecha")
    db.execute(query, {"fecha": fecha_limite})
    db.commit()
    return {"mensaje": f"Registros de auditoría anteriores a {fecha_limite} eliminados"}