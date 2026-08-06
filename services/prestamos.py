from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()

class NuevoPrestamo(BaseModel):
    user_id: int
    material_id: int
    due_date: str

@router.get("/historial")
async def obtener_prestamos(db: Session = Depends(get_db)):
    try:
        query = text("SELECT * FROM vw_loans_effective ORDER BY due_date ASC")
        resultado = db.execute(query).mappings().all()
        return {"prestamos": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/registrar")
async def registrar_prestamo(prestamo: NuevoPrestamo, db: Session = Depends(get_db)):
    try:
        # Ejemplo de cómo insertar un nuevo préstamo en la BD real
        query = text("""
                     INSERT INTO loans (user_id, material_id, loan_date, due_date, registered_by)
                     VALUES (:user_id, :material_id, CURDATE(), :due_date, 1)
                     """)
        db.execute(query, {
            "user_id": prestamo.user_id,
            "material_id": prestamo.material_id,
            "due_date": prestamo.due_date
        })
        db.commit()
        return {"mensaje": "Préstamo registrado correctamente en la base de datos"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))