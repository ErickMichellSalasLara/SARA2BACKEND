from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    database_today = db.execute(text("SELECT CURDATE()")).scalar_one()
    inside_now = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM (
                     SELECT ar.user_id, ar.movement AS last_movement
                     FROM access_records ar
                              INNER JOIN (
                         SELECT user_id, MAX(occurred_at) AS last_time
                         FROM access_records
                         WHERE user_id IS NOT NULL
                           AND result = 'granted'
                         GROUP BY user_id
                     ) latest
                    ON latest.user_id = ar.user_id
                    AND latest.last_time = ar.occurred_at
                 ) t
            WHERE t.last_movement = 'entry';
            """
        )
    ).scalar_one()

    accesses_today = db.execute(
        text("SELECT COUNT(*) FROM access_records WHERE DATE(occurred_at) = CURDATE()")
    ).scalar_one()

    loans_active = db.execute(
        text("SELECT COUNT(*) FROM loans WHERE status IN ('active', 'renewed', 'overdue')")
    ).scalar_one()

    loans_overdue = db.execute(
        text(
            """
            SELECT COUNT(*) FROM loans
            WHERE status = 'overdue'
               OR (status IN ('active', 'renewed') AND due_date < CURDATE())
            """
        )
    ).scalar_one()

    cubicle_rows = db.execute(
        text("SELECT status, COUNT(*) AS total FROM vw_cubicle_status GROUP BY status")
    ).mappings().all()
    occupancy = {"occupied": 0, "reserved": 0, "available": 0, "maintenance": 0}
    for row in cubicle_rows:
        state = str(row["status"]).lower()
        if state in occupancy:
            occupancy[state] = int(row["total"])

    unavailable = occupancy["occupied"] + occupancy["reserved"] + occupancy["maintenance"]
    total_cubicles = sum(occupancy.values())

    affluence_rows = db.execute(
        text("""
             SELECT
                 HOUR(occurred_at) AS hour,
                 COUNT(*) AS value
             FROM access_records
             WHERE DATE(occurred_at)=CURDATE()
               AND movement='entry'
               AND result='granted'
             GROUP BY HOUR(occurred_at)
             ORDER BY HOUR(occurred_at)
             """)
    ).mappings().all()

    affluence = [
        {
        "label": f"{row['hour']:02d}:00",
        "value": row["value"]
        }
        for row in affluence_rows
    ]

    activities = db.execute(
        text(
            """
            SELECT
                ar.id,
                TIME_FORMAT(ar.occurred_at, '%H:%i') AS time,
                COALESCE(u.full_name, 'Usuario desconocido') AS user,
                CASE ar.movement WHEN 'entry' THEN 'Acceso' ELSE 'Salida' END AS action,
                d.name AS resource,
                CASE ar.result WHEN 'granted' THEN 'Permitido' ELSE 'Denegado' END AS status
            FROM access_records ar
            LEFT JOIN users u ON u.id = ar.user_id
            JOIN devices d ON d.id = ar.device_id
            ORDER BY ar.occurred_at DESC
            LIMIT 8
            """
        )
    ).mappings().all()

    alerts = db.execute(
        text(
            """
            SELECT id, level, title, description,
                   DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') AS time
            FROM system_alerts
            WHERE is_resolved = FALSE
            ORDER BY created_at DESC
            LIMIT 6
            """
        )
    ).mappings().all()

    return {
        "metrics": [
            {
                "id": "inside",
                "title": "Usuarios dentro",
                "value": int(inside_now),
                "detail": "En este momento",
                "trend": "Lecturas RFID",
                "tone": "purple",
                "icon": "users",
            },
            {
                "id": "accesses",
                "title": "Accesos de hoy",
                "value": int(accesses_today),
                "detail": database_today.isoformat(),
                "trend": "Entradas y salidas",
                "tone": "blue",
                "icon": "access",
            },
            {
                "id": "occupancy",
                "title": "Cubículos no disponibles",
                "value": f"{unavailable} / {total_cubicles}",
                "detail": "Ocupados, reservados o mantenimiento",
                "trend": f"{occupancy['available']} disponibles",
                "tone": "green",
                "icon": "calendar",
            },
            {
                "id": "loans",
                "title": "Préstamos activos",
                "value": int(loans_active),
                "detail": f"{loans_overdue} requieren atención",
                "trend": f"{loans_overdue} vencidos",
                "tone": "orange",
                "icon": "book",
            },
        ],
        "affluence": affluence,
        "occupancy": occupancy,
        "activities": [dict(row) for row in activities],
        "alerts": [dict(row) for row in alerts],
    }
