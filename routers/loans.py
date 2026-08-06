from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from core.serialization import rows_to_dicts
from database import get_db
from dependencies import require_staff
from schemas.dto import LoanCreate

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])

STATUS_LABELS = {
    "active": "Activo",
    "overdue": "Vencido",
    "renewed": "Renovado",
    "returned": "Devuelto",
    "lost": "Perdido",
    "cancelled": "Cancelado",
}


@router.get("/historial")
def loan_history(
    _: dict = Depends(require_staff),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("SELECT * FROM vw_loans_effective ORDER BY due_date ASC")
    ).mappings().all()

    loans = []
    for row in rows_to_dicts(rows):
        raw_status = str(row.get("status", "active"))
        loans.append(
            {
                "id": row.get("id"),
                "user_id": row.get("user_id"),
                "material_id": row.get("material_id"),
                "user": row.get("user_name"),
                "enrollment": row.get("enrollment"),
                "resource": row.get("resource"),
                "code": row.get("resource_code"),
                "start": row.get("loan_date"),
                "due": row.get("due_date"),
                "returnDate": row.get("return_date"),
                "statusCode": raw_status,
                "status": STATUS_LABELS.get(raw_status, raw_status),
                "renewalCount": row.get("renewal_count", 0),
            }
        )

    return {"prestamos": loans}


@router.get("/catalogos")
def loan_catalogs(
    _: dict = Depends(require_staff),
    db: Session = Depends(get_db),
):
    users = db.execute(
        text(
            """
            SELECT id, full_name AS name, enrollment
            FROM users
            WHERE status = 'active'
            ORDER BY full_name
            """
        )
    ).mappings().all()
    materials = db.execute(
        text(
            """
            SELECT id, resource_code AS code, title
            FROM materials
            WHERE status = 'available'
            ORDER BY title
            """
        )
    ).mappings().all()
    return {
        "users": rows_to_dicts(users),
        "materials": rows_to_dicts(materials),
    }


@router.post("/registrar", status_code=status.HTTP_201_CREATED)
def create_loan(
    payload: LoanCreate,
    current_user: dict = Depends(require_staff),
    db: Session = Depends(get_db),
):
    today = db.execute(text("SELECT CURDATE()")).scalar_one()
    if payload.due_date < today:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La fecha límite no puede ser anterior a hoy.",
        )

    user_exists = db.execute(
        text("SELECT COUNT(*) FROM users WHERE id = :id AND status = 'active'"),
        {"id": payload.user_id},
    ).scalar_one()
    if not user_exists:
        raise HTTPException(status_code=404, detail="El usuario no existe o está inactivo.")

    material = db.execute(
        text("SELECT status FROM materials WHERE id = :id FOR UPDATE"),
        {"id": payload.material_id},
    ).scalar_one_or_none()
    if material is None:
        raise HTTPException(status_code=404, detail="El material no existe.")
    if material != "available":
        raise HTTPException(status_code=409, detail="El material no está disponible.")

    try:
        result = db.execute(
            text(
                """
                INSERT INTO loans (
                    user_id, material_id, loan_date, due_date, status, registered_by
                ) VALUES (
                    :user_id, :material_id, CURDATE(), :due_date, 'active', :registered_by
                )
                """
            ),
            {
                "user_id": payload.user_id,
                "material_id": payload.material_id,
                "due_date": payload.due_date,
                "registered_by": current_user["id"],
            },
        )
        db.execute(
            text(
                """
                INSERT INTO audit_logs (
                    actor_user_id, action, module, entity_type, entity_id, record_label
                ) VALUES (
                    :actor, 'Registró un préstamo', 'Préstamos',
                    'loan', :entity_id, :label
                )
                """
            ),
            {
                "actor": current_user["id"],
                "entity_id": str(result.lastrowid),
                "label": f"Material {payload.material_id}",
            },
        )
        db.commit()
    except (IntegrityError, DBAPIError) as exc:
        db.rollback()
        raw_message = str(getattr(exc, "orig", exc))
        detail = (
            "El recurso no se encuentra disponible."
            if "recurso no se encuentra disponible" in raw_message.lower()
            else "No fue posible registrar el préstamo."
        )
        raise HTTPException(status_code=409, detail=detail) from exc

    return {"message": "Préstamo registrado correctamente.", "id": result.lastrowid}


@router.put("/devolver/{loan_id}")
def return_loan(
    loan_id: int,
    current_user: dict = Depends(require_staff),
    db: Session = Depends(get_db),
):
    loan = db.execute(
        text("SELECT material_id, status FROM loans WHERE id = :id"),
        {"id": loan_id},
    ).mappings().first()
    if not loan:
        raise HTTPException(status_code=404, detail="El préstamo no existe.")
    if loan["status"] not in ("active", "renewed", "overdue"):
        raise HTTPException(
            status_code=409,
            detail="El préstamo no se encuentra activo para registrar una devolución.",
        )

    db.execute(
        text(
            """
            UPDATE loans
            SET status = 'returned', return_date = CURDATE()
            WHERE id = :id
            """
        ),
        {"id": loan_id},
    )
    db.execute(
        text(
            """
            INSERT INTO audit_logs (
                actor_user_id, action, module, entity_type, entity_id, record_label
            ) VALUES (
                :actor, 'Registró una devolución', 'Préstamos', 'loan', :entity_id, :label
            )
            """
        ),
        {
            "actor": current_user["id"],
            "entity_id": str(loan_id),
            "label": f"Préstamo {loan_id}",
        },
    )
    db.commit()
    return {"message": "Devolución registrada correctamente."}


@router.put("/renovar/{loan_id}")
def renew_loan(
    loan_id: int,
    current_user: dict = Depends(require_staff),
    db: Session = Depends(get_db),
):
    loan = db.execute(
        text("SELECT status, renewal_count, due_date FROM loans WHERE id = :id"),
        {"id": loan_id},
    ).mappings().first()
    if not loan:
        raise HTTPException(status_code=404, detail="El préstamo no existe.")
    if loan["status"] not in ("active", "renewed", "overdue"):
        raise HTTPException(status_code=409, detail="El préstamo no puede renovarse.")
    if int(loan["renewal_count"]) >= 3:
        raise HTTPException(status_code=409, detail="Se alcanzó el límite de renovaciones.")

    loan_days = db.execute(
        text(
            """
            SELECT CAST(setting_value AS UNSIGNED)
            FROM system_settings WHERE setting_key = 'default_loan_days'
            """
        )
    ).scalar_one_or_none() or 7

    today = db.execute(text("SELECT CURDATE()")).scalar_one()
    base_date = max(loan["due_date"], today)
    new_due_date = base_date + timedelta(days=int(loan_days))

    db.execute(
        text(
            """
            UPDATE loans
            SET status = 'renewed', renewal_count = renewal_count + 1,
                due_date = :due_date
            WHERE id = :id
            """
        ),
        {"id": loan_id, "due_date": new_due_date},
    )
    db.execute(
        text(
            """
            INSERT INTO audit_logs (
                actor_user_id, action, module, entity_type, entity_id, record_label
            ) VALUES (
                :actor, 'Renovó un préstamo', 'Préstamos',
                'loan', :entity_id, :label
            )
            """
        ),
        {
            "actor": current_user["id"],
            "entity_id": str(loan_id),
            "label": f"Préstamo {loan_id}",
        },
    )
    db.commit()
    return {"message": "Préstamo renovado correctamente."}
