from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

# Consulta directa usando la Vista vw_access_records generada en tu script
@router.get("/historial")
def obtener_historial_accesos(db: Session = Depends(get_db)):
    query = text("""
                 SELECT id, occurred_at, user_name, enrollment, movement, reader, result
                 FROM vw_access_records
                 ORDER BY occurred_at DESC
                 """)
    resultados = db.execute(query).mappings().all()
    return {"accesos": resultados}