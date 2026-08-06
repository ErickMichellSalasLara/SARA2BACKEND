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
