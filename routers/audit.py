from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.serialization import rows_to_dicts
from database import get_db
from dependencies import require_admin
from schemas.dto import AuditCreate

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("/historial")
def get_audit_history(db: Session = Depends(get_db)):
    query = text("""
                 SELECT
                     u.full_name AS administrador,
                     a.action AS accion,
                     a.module AS modulo,
                     a.record_label AS registro,
                     a.created_at AS fecha,
                     a.ip_address AS direccion_ip
                 FROM audit_logs a
                          LEFT JOIN users u ON a.actor_user_id = u.id
                 ORDER BY a.created_at DESC
                     LIMIT 100
                 """)

    rows = db.execute(query).mappings().all()

    # Formatear las fechas para que no rompan el JSON en React
    resultados = []
    for row in rows:
        dict_row = dict(row)
        if dict_row["fecha"]:
            dict_row["fecha"] = dict_row["fecha"].strftime("%Y-%m-%d %H:%M:%S")
        # Por si hay campos nulos, mandar un string vacío
        dict_row["registro"] = dict_row["registro"] or "N/A"
        dict_row["direccion_ip"] = dict_row["direccion_ip"] or "Desconocida"
        resultados.append(dict_row)

    return {"auditoria": resultados}


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
