from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

# NOTA: main.py ya le pone el prefix="/api/usuarios"
router = APIRouter(tags=["Usuarios"])

class UsuarioDTO(BaseModel):
    name: str
    email: str
    enrollment: str
    role_id: int
    status: str = "active"

class EstadoDTO(BaseModel):
    status: str

@router.get("/")
def obtener_usuarios(db: Session = Depends(get_db)):
    # Consulta uniendo users y roles[cite: 1]
    query = text("""
                 SELECT u.id, u.full_name AS name, u.email, u.enrollment, r.name AS role, u.status
                 FROM users u
                          JOIN roles r ON u.role_id = r.id
                 """)
    rows = db.execute(query).fetchall()

    # Convertimos a JSON
    usuarios = [
        {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "enrollment": row[3],
            "role": row[4],
            "status": row[5]
        } for row in rows
    ]
    return {"usuarios": usuarios}

@router.post("/registrar")
def registrar_usuario(user: UsuarioDTO, db: Session = Depends(get_db)):
    # Contraseña genérica (dummy_hash) requerida por la base de datos[cite: 1]
    dummy_hash = "pbkdf2_sha256$600000$dummy_hash_aqui"

    query = text("""
                 INSERT INTO users (full_name, email, enrollment, password_hash, role_id, status, email_verified_at)
                 VALUES (:name, :email, :enrollment, :password_hash, :role_id, :status, NOW())
                 """)

    valores = {
        "name": user.name,
        "email": user.email,
        "enrollment": user.enrollment,
        "password_hash": dummy_hash,
        "role_id": user.role_id,
        "status": user.status
    }

    result = db.execute(query, valores)
    db.commit() # ¡Importante guardar los cambios!

    return {"id": result.lastrowid, "mensaje": "Usuario registrado exitosamente"}

@router.put("/estado/{user_id}")
def cambiar_estado(user_id: int, estado: EstadoDTO, db: Session = Depends(get_db)):
    query = text("UPDATE users SET status = :status WHERE id = :id") # Actualiza el estado del usuario[cite: 1]
    db.execute(query, {"status": estado.status, "id": user_id})
    db.commit() # Guardamos los cambios

    return {"mensaje": "Estado actualizado correctamente"}