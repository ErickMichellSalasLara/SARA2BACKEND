from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.serialization import rows_to_dicts
from database import get_db
from dependencies import require_admin
from schemas.dto import AuditCreate

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("/historial")
def audit_history(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("SELECT * FROM vw_audit_records ORDER BY occurred_at DESC")
    ).mappings().all()
    return {"auditoria": rows_to_dicts(rows)}


@router.post("/registrar", status_code=status.HTTP_201_CREATED)
def register_audit(
    payload: AuditCreate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    result = db.execute(
        text(
            """
            INSERT INTO audit_logs (
                actor_user_id, action, module, record_label
            ) VALUES (:actor, :action, :module, :record)
            """
        ),
        {
            "actor": current_user["id"],
            "action": payload.action,
            "module": payload.module,
            "record": payload.record,
        },
    )
    db.commit()
    return {"message": "Registro de auditoría creado.", "id": result.lastrowid}
