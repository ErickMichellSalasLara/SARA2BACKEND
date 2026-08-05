from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

@router.get("/historial")
async def obtener_accesos(db: Session = Depends(get_db)):
    try:
        # Leemos directamente de la vista que une los usuarios con las tarjetas y dispositivos
        query = text("SELECT * FROM vw_access_records ORDER BY occurred_at DESC")
        resultado = db.execute(query).mappings().all()
        return {"accesos": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))