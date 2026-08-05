from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

class AuditoriaCreate(BaseModel):
    admin: str
    action: str
    module: str
    record: str

@router.get("/historial")
async def obtener_historial(db: Session = Depends(get_db)):
    try:
        # Consultamos la base de datos real usando la vista preparada
        query = text("SELECT * FROM vw_audit_records ORDER BY occurred_at DESC")
        resultado = db.execute(query).mappings().all()
        return {"auditoria": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/registrar")
async def registrar_auditoria(auditoria: AuditoriaCreate, db: Session = Depends(get_db)):
    try:
        # Insertamos el nuevo registro en la base de datos real
        query = text("""
                     INSERT INTO audit_logs (actor_user_id, action, module, record_label, ip_address)
                     VALUES (:actor, :action, :module, :record, :ip)
                     """)
        # Nota: Ponemos actor_user_id = 1 (Admin demo) de forma temporal hasta que conectes el login real
        db.execute(query, {
            "actor": 1,
            "action": auditoria.action,
            "module": auditoria.module,
            "record": auditoria.record,
            "ip": "127.0.0.1"
        })
        db.commit()
        return {"mensaje": "Registro exitoso en base de datos"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))