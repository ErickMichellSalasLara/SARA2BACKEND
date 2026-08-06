from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.security import hash_password
from core.serialization import rows_to_dicts
from database import get_db
from dependencies import require_admin
from schemas.dto import UserCreate, UserStatusUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

ROLE_LABELS = {
    "student": "Estudiante",
    "teacher": "Docente",
    "librarian": "Bibliotecario",
    "admin": "Administrador",
}
STATUS_LABELS = {
    "active": "Activo",
    "inactive": "Inactivo",
    "blocked": "Bloqueado",
    "pending": "Pendiente",
}


@router.get("")
def list_users(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text(
            """
            SELECT u.id, u.full_name AS name, u.email, u.enrollment,
                   r.code AS role_code, u.status AS status_code
            FROM users u
            JOIN roles r ON r.id = u.role_id
            ORDER BY u.full_name
            """
        )
    ).mappings().all()

    users = []
    for row in rows_to_dicts(rows):
        role_code = str(row.pop("role_code"))
        status_code = str(row.pop("status_code"))
        users.append(
            {
                **row,
                "roleCode": role_code,
                "role": ROLE_LABELS.get(role_code, role_code),
                "statusCode": status_code,
                "status": STATUS_LABELS.get(status_code, status_code),
            }
        )
    return {"users": users}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    role_id = db.execute(
        text("SELECT id FROM roles WHERE code = :code"),
        {"code": payload.role},
    ).scalar_one_or_none()
    if role_id is None:
        raise HTTPException(status_code=422, detail="El rol seleccionado no existe.")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO users (
                    full_name, email, enrollment, password_hash,
                    role_id, status, email_verified_at
                ) VALUES (
                    :name, :email, :enrollment, :password_hash,
                    :role_id, 'active', NOW()
                )
                """
            ),
            {
                "name": " ".join(payload.name.split()),
                "email": str(payload.email).lower(),
                "enrollment": payload.enrollment.upper(),
                "password_hash": hash_password(payload.password),
                "role_id": role_id,
            },
        )
        db.execute(
            text(
                """
                INSERT INTO audit_logs (
                    actor_user_id, action, module, entity_type, entity_id, record_label
                ) VALUES (
                    :actor, 'Creó un usuario', 'Usuarios', 'user', :entity_id, :record
                )
                """
            ),
            {
                "actor": current_user["id"],
                "entity_id": str(result.lastrowid),
                "record": payload.enrollment.upper(),
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="El correo o la matrícula ya están registrados.",
        ) from exc

    return {"message": "Usuario creado correctamente.", "id": result.lastrowid}


@router.patch("/{user_id}/status")
def change_status(
    user_id: int,
    payload: UserStatusUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if user_id == current_user["id"] and payload.status != "active":
        raise HTTPException(
            status_code=409,
            detail="No puedes desactivar tu propia cuenta administrativa.",
        )

    result = db.execute(
        text("UPDATE users SET status = :status WHERE id = :id"),
        {"status": payload.status, "id": user_id},
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="El usuario no existe.")

    db.execute(
        text(
            """
            INSERT INTO audit_logs (
                actor_user_id, action, module, entity_type, entity_id, record_label
            ) VALUES (
                :actor, 'Cambió el estado de un usuario', 'Usuarios',
                'user', :entity_id, :record
            )
            """
        ),
        {
            "actor": current_user["id"],
            "entity_id": str(user_id),
            "record": payload.status,
        },
    )
    db.commit()
    return {"message": "Estado actualizado correctamente."}
