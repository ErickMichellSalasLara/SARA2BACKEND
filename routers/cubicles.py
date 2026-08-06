from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.serialization import rows_to_dicts
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/cubicles", tags=["Cubículos"])


@router.get("/status")
def cubicle_status(
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        rows = db.execute(
            text("SELECT * FROM vw_cubicle_status ORDER BY id")
        ).mappings().all()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No fue posible consultar la vista vw_cubicle_status.",
        ) from exc

    cubicles = []
    occupancy = {
        "occupied": 0,
        "reserved": 0,
        "available": 0,
        "maintenance": 0,
    }

    for row in rows_to_dicts(rows):
        status = str(row.get("status", "available")).lower()
        if status == "disabled":
            status = "maintenance"
        if status in occupancy:
            occupancy[status] += 1

        cubicles.append(
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "location": row.get("location"),
                "capacity": row.get("capacity"),
                "status": status,
                "currentSchedule": row.get("current_schedule"),
                "nextReservation": row.get("next_reservation"),
            }
        )

    return {
        "cubicles": cubicles,
        "occupancy": occupancy,
        "updatedAt": str(db.execute(text("SELECT NOW()")).scalar_one()),
    }
