from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from database import get_db

router = APIRouter()

class PrestamoCreate(BaseModel):
    matricula: str
    material: str
    codigo: str

# ---------------------------------------------------------
# CREATE (Insertar préstamo)
# ---------------------------------------------------------
@router.post("/registrar")
def registrar_prestamo(loan: LoanCreate, db: Session = Depends(get_db)):
    query = text("""
                 INSERT INTO loans (user_id, material_id, loan_date, due_date, status, registered_by)
                 VALUES (:user_id, :material_id, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'active', :registered_by)
                 """)
    db.execute(query, {
        "user_id": loan.user_id,
        "material_id": loan.material_id,
        "registered_by": loan.registered_by
    })
    db.commit()
    return {"mensaje": "Préstamo registrado exitosamente"}

# ---------------------------------------------------------
# UPDATE (Actualizar a devuelto)
# ---------------------------------------------------------
@router.put("/devolver/{loan_id}")
def devolver_prestamo(loan_id: int, db: Session = Depends(get_db)):
    query = text("""
                 UPDATE loans
                 SET status = 'returned', return_date = CURDATE()
                 WHERE id = :id
                 """)
    db.execute(query, {"id": loan_id})
    db.commit()
    return {"mensaje": "Préstamo devuelto correctamente"}

# ---------------------------------------------------------
# JOIN (Obtener préstamos activos uniendo con Usuarios)
# ---------------------------------------------------------
@router.get("/activos")
def obtener_prestamos_activos(db: Session = Depends(get_db)):
    query = text("""
                 SELECT u.full_name, u.enrollment, m.title AS resource, l.id, l.loan_date, l.due_date, l.status
                 FROM loans l
                          INNER JOIN users u ON u.id = l.user_id
                          INNER JOIN materials m ON m.id = l.material_id
                 WHERE l.status = 'active'
                 """)
    resultados = db.execute(query).mappings().all()
    return {"prestamos_activos": resultados}

# ---------------------------------------------------------
# SUBCONSULTA (Identificar usuarios morosos/vencidos)
# ---------------------------------------------------------
@router.get("/morosos")
def obtener_morosos(db: Session = Depends(get_db)):
    query = text("""
                 SELECT full_name, email, enrollment
                 FROM users
                 WHERE id IN (
                     SELECT user_id
                     FROM loans
                     WHERE status = 'overdue'
                 )
                 """)
    resultados = db.execute(query).mappings().all()
    return {"usuarios_morosos": resultados}

# ---------------------------------------------------------
# GROUP BY y HAVING (Lectores frecuentes > 3 préstamos)
# ---------------------------------------------------------
@router.get("/frecuentes")
def obtener_usuarios_frecuentes(db: Session = Depends(get_db)):
    query = text("""
                 SELECT user_id, COUNT(*) AS total_prestamos
                 FROM loans
                 GROUP BY user_id
                 HAVING COUNT(*) >= 1
                 """)
    resultados = db.execute(query).mappings().all()
    return {"usuarios_frecuentes": resultados}