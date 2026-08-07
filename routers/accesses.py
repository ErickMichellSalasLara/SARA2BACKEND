from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.serialization import rows_to_dicts
from database import get_db
from dependencies import require_admin

router = APIRouter(prefix="/accesos", tags=["Accesos"])


@router.get("/historial")
def access_history(
        _: dict = Depends(require_admin),
        db: Session = Depends(get_db),
):
    rows = db.execute(
        text("SELECT * FROM vw_access_records ORDER BY occurred_at DESC")
    ).mappings().all()

    records = []
    for row in rows_to_dicts(rows):
        occurred_at = row.get("occurred_at")
        records.append(
            {
                "id": row.get("id"),
                "name": row.get("user_name"),
                "enrollment": row.get("enrollment"),
                "time": str(occurred_at).replace("T", " ") if occurred_at else "",
                "movement": "Entrada" if row.get("movement") == "entry" else "Salida",
                "reader": row.get("reader"),
                "status": "Permitido" if row.get("result") == "granted" else "Denegado",
                "reason": row.get("reason"),
            }
        )

    return {"accesos": records}


@router.get("/estadisticas")
def access_statistics(
        _: dict = Depends(require_admin),
        db: Session = Depends(get_db),
):
    # 1. Usuarios dentro ahora (último movimiento fue entrada)
    inside_now = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM (
                     SELECT ar.user_id,
                            SUBSTRING_INDEX(
                                    GROUP_CONCAT(ar.movement ORDER BY ar.occurred_at DESC),
                                    ',', 1
                            ) AS last_movement
                     FROM access_records ar
                     WHERE ar.user_id IS NOT NULL AND ar.result = 'granted'
                     GROUP BY ar.user_id
                 ) latest
            WHERE latest.last_movement = 'entry'
            """
        )
    ).scalar_one_or_none() or 0

    # 2. Total de accesos hoy
    accesses_today = db.execute(
        text("SELECT COUNT(*) FROM access_records WHERE DATE(occurred_at) = CURDATE()")
    ).scalar_one_or_none() or 0

    # 3. Accesos denegados hoy
    denied_today = db.execute(
        text("SELECT COUNT(*) FROM access_records WHERE DATE(occurred_at) = CURDATE() AND result = 'denied'")
    ).scalar_one_or_none() or 0

    return {
        "dentroAhora": int(inside_now),
        "accesosHoy": int(accesses_today),
        "accesosDenegados": int(denied_today)
    }