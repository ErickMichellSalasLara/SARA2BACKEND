from __future__ import annotations

from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from core.serialization import rows_to_dicts
from database import get_db
from dependencies import get_current_user, require_admin
from schemas.dto import ReservationCreate

router = APIRouter(prefix="/reservations", tags=["Reservas"])
calendar_router = APIRouter(prefix="/calendario", tags=["Calendario"])

ACTIVE_STATUSES = ("pending", "confirmed", "active")
STATUS_LABELS = {
    "pending": "Pendiente",
    "confirmed": "Reservado",
    "active": "Ocupado",
    "completed": "Completado",
    "cancelled": "Cancelado",
    "expired": "Expirado",
    "no_show": "No utilizado",
}


def _time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _get_setting(db: Session, key: str, fallback: str) -> str:
    value = db.execute(
        text("SELECT setting_value FROM system_settings WHERE setting_key = :key"),
        {"key": key},
    ).scalar_one_or_none()
    return str(value or fallback)


def _validate_reservation(db: Session, payload: ReservationCreate, user_id: int) -> None:
    opening = time.fromisoformat(_get_setting(db, "service_start_time", "07:30:00"))
    closing = time.fromisoformat(_get_setting(db, "service_end_time", "16:00:00"))
    max_minutes = int(_get_setting(db, "maximum_reservation_minutes", "90"))

    current = db.execute(
        text("SELECT CURDATE() AS today, CURTIME() AS hora_actual")
    ).mappings().one()

    if payload.reservation_date < current["today"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No puedes crear una reserva en una fecha pasada.",
        )
    if (
            payload.reservation_date == current["today"]
            and payload.start_time <= current["hora_actual"]
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora inicial debe ser posterior a la hora actual.",
        )

    if payload.start_time < opening or payload.end_time > closing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las reservas solo están permitidas de 07:30 a 16:00.",
        )
    if payload.start_time >= payload.end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La hora final debe ser posterior a la hora inicial.",
        )
    duration = _time_to_minutes(payload.end_time) - _time_to_minutes(payload.start_time)
    if duration > max_minutes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La reserva no puede durar más de {max_minutes} minutos.",
        )

    schedule = db.execute(
        text(
            """
            SELECT is_open, opening_time, closing_time
            FROM service_schedules
            WHERE day_of_week = WEEKDAY(:reservation_date) + 1
            """
        ),
        {"reservation_date": payload.reservation_date},
    ).mappings().first()

    print(type(schedule["opening_time"]))
    print(schedule["closing_time"])
    print(schedule["opening_time"])
    print(type(schedule["closing_time"]))

    if not schedule or not schedule["is_open"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay servicio el día seleccionado.",
        )
    if (
        payload.start_time < schedule["opening_time"]
        or payload.end_time > schedule["closing_time"]
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La reserva está fuera del horario de servicio de ese día.",
        )

    is_holiday = db.execute(
        text(
            "SELECT COUNT(*) FROM holidays WHERE holiday_date = :date AND is_closed = TRUE"
        ),
        {"date": payload.reservation_date},
    ).scalar_one()
    if is_holiday:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se permiten reservas durante un cierre institucional.",
        )

    cubicle = db.execute(
        text(
            """
            SELECT id, name, capacity, operational_status, is_active
            FROM cubicles WHERE id = :cubicle_id
            FOR UPDATE
            """
        ),
        {"cubicle_id": payload.cubicle_id},
    ).mappings().first()
    if not cubicle:
        raise HTTPException(status_code=404, detail="El cubículo no existe.")
    if not cubicle["is_active"] or cubicle["operational_status"] != "available":
        raise HTTPException(status_code=409, detail="El cubículo no está disponible.")
    if payload.number_of_people > cubicle["capacity"]:
        raise HTTPException(
            status_code=422,
            detail="El número de personas excede la capacidad del cubículo.",
        )

    user_active = db.execute(
        text("SELECT COUNT(*) FROM users WHERE id = :id AND status = 'active'"),
        {"id": user_id},
    ).scalar_one()
    if not user_active:
        raise HTTPException(status_code=409, detail="El usuario no está activo.")

    overlap = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM reservations
            WHERE cubicle_id = :cubicle_id
              AND reservation_date = :reservation_date
              AND status IN ('pending', 'confirmed', 'active')
              AND :start_time < end_time
              AND :end_time > start_time
            """
        ),
        {
            "cubicle_id": payload.cubicle_id,
            "reservation_date": payload.reservation_date,
            "start_time": payload.start_time,
            "end_time": payload.end_time,
        },
    ).scalar_one()
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El cubículo ya tiene una reserva en ese horario.",
        )


def _reservation_database_error(exc: Exception) -> str:
    raw_message = str(getattr(exc, "orig", exc))
    known_messages = (
        "No se permiten reservas en fechas u horarios pasados",
        "Las reservas solo están permitidas",
        "La hora final debe ser posterior",
        "La reserva excede",
        "El sistema no presta servicio",
        "No se permiten reservas",
        "El usuario no tiene una cuenta activa",
        "El cubículo no se encuentra disponible",
        "El número de personas excede",
        "El cubículo ya tiene una reserva",
        "El cubículo tiene mantenimiento",
    )
    for message in known_messages:
        if message in raw_message:
            start = raw_message.index(message)
            return raw_message[start:].strip(" '\")")
    return "No fue posible guardar la reserva en la base de datos."


def _reservation_rows(db: Session):
    return db.execute(
        text(
            """
            SELECT
                r.id,
                r.user_id,
                r.cubicle_id,
                c.name AS room,
                u.full_name AS user,
                r.reservation_date AS date,
                r.start_time,
                r.end_time,
                r.status,
                r.purpose,
                r.number_of_people
            FROM reservations r
            JOIN users u ON u.id = r.user_id
            JOIN cubicles c ON c.id = r.cubicle_id
            ORDER BY r.reservation_date DESC, r.start_time DESC
            """
        )
    ).mappings().all()


@router.get("")
def list_reservations(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reservations = []
    for row in rows_to_dicts(_reservation_rows(db)):
        start_value = str(row.pop("start_time", ""))[:5]
        end_value = str(row.pop("end_time", ""))[:5]
        raw_status = row["status"]
        row["time"] = f"{start_value} - {end_value}"
        row["statusCode"] = raw_status
        row["status"] = STATUS_LABELS.get(raw_status, raw_status)
        reservations.append(row)
    return {"reservations": reservations}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_user_id = payload.user_id if current_user["role"] == "admin" else current_user["id"]
    if target_user_id is None:
        target_user_id = current_user["id"]

    _validate_reservation(db, payload, target_user_id)

    try:
        result = db.execute(
            text(
                """
                INSERT INTO reservations (
                    user_id, cubicle_id, reservation_date, start_time, end_time,
                    status, purpose, number_of_people, source, created_by
                ) VALUES (
                    :user_id, :cubicle_id, :reservation_date, :start_time, :end_time,
                    'confirmed', :purpose, :number_of_people, :source, :created_by
                )
                """
            ),
            {
                "user_id": target_user_id,
                "cubicle_id": payload.cubicle_id,
                "reservation_date": payload.reservation_date,
                "start_time": payload.start_time,
                "end_time": payload.end_time,
                "purpose": payload.purpose,
                "number_of_people": payload.number_of_people,
                "source": "admin" if current_user["role"] == "admin" else "student",
                "created_by": current_user["id"],
            },
        )
        db.execute(
            text(
                """
                INSERT INTO audit_logs (
                    actor_user_id, action, module, entity_type, entity_id, record_label
                )
                SELECT :actor, 'Creó una reserva', 'Reservas', 'reservation',
                       :entity_id, name
                FROM cubicles WHERE id = :cubicle_id
                """
            ),
            {
                "actor": current_user["id"],
                "entity_id": str(result.lastrowid),
                "cubicle_id": payload.cubicle_id,
            },
        )
        db.commit()
    except (IntegrityError, DBAPIError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_reservation_database_error(exc),
        ) from exc

    return {"message": "Reserva creada correctamente.", "id": result.lastrowid}


@router.patch("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT user_id, status FROM reservations WHERE id = :id"),
        {"id": reservation_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="La reserva no existe.")
    if current_user["role"] != "admin" and row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="No puedes cancelar esta reserva.")
    if row["status"] not in ACTIVE_STATUSES:
        raise HTTPException(status_code=409, detail="La reserva ya no puede cancelarse.")

    db.execute(
        text(
            """
            UPDATE reservations
            SET status = 'cancelled', cancelled_by = :user_id,
                cancelled_at = NOW(), cancellation_reason = 'Cancelación desde S.A.R.A.'
            WHERE id = :id
            """
        ),
        {"id": reservation_id, "user_id": current_user["id"]},
    )
    db.execute(
        text(
            """
            INSERT INTO audit_logs (
                actor_user_id, action, module, entity_type, entity_id, record_label
            ) VALUES (
                :actor, 'Canceló una reserva', 'Reservas',
                'reservation', :entity_id, :label
            )
            """
        ),
        {
            "actor": current_user["id"],
            "entity_id": str(reservation_id),
            "label": f"Reserva {reservation_id}",
        },
    )
    db.commit()
    return {"message": "Reserva cancelada correctamente."}


@calendar_router.get("/dias-festivos")
def holidays(
    year: int = Query(default_factory=lambda: date.today().year, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text(
            """
            SELECT holiday_date AS fecha, name AS motivo, is_closed
            FROM holidays
            WHERE YEAR(holiday_date) = :year
            ORDER BY holiday_date
            """
        ),
        {"year": year},
    ).mappings().all()
    return {"festivos": rows_to_dicts(rows)}


@calendar_router.get("/eventos")
def calendar_events(
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text(
            """
            SELECT event_id AS id, title,
                   start_datetime AS start, end_datetime AS end, status
            FROM vw_calendar_events
            ORDER BY start_datetime
            """
        )
    ).mappings().all()
    return {"eventos": rows_to_dicts(rows)}


@calendar_router.get("/estado-cubiculos")
def calendar_cubicles(
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("SELECT * FROM vw_cubicle_status ORDER BY id")).mappings().all()
    return {"cubiculos": rows_to_dicts(rows)}


@calendar_router.get("/historial-bd")
def calendar_history(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return {"reservas_bd": rows_to_dicts(_reservation_rows(db))}
