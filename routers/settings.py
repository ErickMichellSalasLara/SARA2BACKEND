from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config import ALLOWED_EMAIL_DOMAIN
from database import get_db
from dependencies import require_admin
from schemas.dto import SettingsUpdate

router = APIRouter(prefix="/configuracion", tags=["Configuración"])

KEY_MAP = {
    "systemName": "system_name",
    "serviceStart": "service_start_time",
    "serviceEnd": "service_end_time",
    "reservationDuration": "maximum_reservation_minutes",
    "tolerance": "reservation_tolerance_minutes",
    "loanDays": "default_loan_days",
    "allowedDomain": "allowed_email_domain",
    "emailNotifications": "email_notifications",
    "deniedAccessAlerts": "denied_access_alerts",
    "overdueAlerts": "overdue_loan_alerts",
}


def _as_bool(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@router.get("")
def get_settings(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text("SELECT setting_key, setting_value FROM system_settings")
    ).mappings().all()
    values = {row["setting_key"]: row["setting_value"] for row in rows}

    return {
        "settings": {
            "systemName": values.get("system_name", "S.A.R.A."),
            "serviceStart": str(values.get("service_start_time", "07:30"))[:5],
            "serviceEnd": str(values.get("service_end_time", "16:00"))[:5],
            "reservationDuration": int(values.get("maximum_reservation_minutes", 90)),
            "tolerance": int(values.get("reservation_tolerance_minutes", 15)),
            "loanDays": int(values.get("default_loan_days", 7)),
            "allowedDomain": values.get("allowed_email_domain", "@utr.edu.mx"),
            "emailNotifications": _as_bool(values.get("email_notifications", "true")),
            "deniedAccessAlerts": _as_bool(values.get("denied_access_alerts", "true")),
            "overdueAlerts": _as_bool(values.get("overdue_loan_alerts", "true")),
        }
    }


@router.put("")
def update_settings(
    payload: SettingsUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.allowedDomain.strip().lower() != ALLOWED_EMAIL_DOMAIN:
        raise HTTPException(
            status_code=422,
            detail=f"El dominio institucional debe permanecer como {ALLOWED_EMAIL_DOMAIN}.",
        )

    if payload.serviceStart >= payload.serviceEnd:
        raise HTTPException(
            status_code=422,
            detail="La hora de apertura debe ser anterior a la hora de cierre.",
        )
    # Institutional rule requested for the current S.A.R.A. implementation.
    if payload.serviceStart.strftime("%H:%M") != "07:30" or payload.serviceEnd.strftime("%H:%M") != "16:00":
        raise HTTPException(
            status_code=422,
            detail="El horario institucional debe permanecer de 07:30 a 16:00.",
        )

    values = {
        "systemName": payload.systemName,
        "serviceStart": payload.serviceStart.strftime("%H:%M:%S"),
        "serviceEnd": payload.serviceEnd.strftime("%H:%M:%S"),
        "reservationDuration": str(payload.reservationDuration),
        "tolerance": str(payload.tolerance),
        "loanDays": str(payload.loanDays),
        "allowedDomain": payload.allowedDomain.lower(),
        "emailNotifications": str(payload.emailNotifications).lower(),
        "deniedAccessAlerts": str(payload.deniedAccessAlerts).lower(),
        "overdueAlerts": str(payload.overdueAlerts).lower(),
    }

    for field, setting_key in KEY_MAP.items():
        db.execute(
            text(
                """
                UPDATE system_settings
                SET setting_value = :value, updated_by = :user_id
                WHERE setting_key = :key
                """
            ),
            {
                "value": values[field],
                "user_id": current_user["id"],
                "key": setting_key,
            },
        )

    db.execute(
        text(
            """
            INSERT INTO audit_logs (
                actor_user_id, action, module, entity_type, entity_id, record_label
            ) VALUES (
                :actor, 'Modificó la configuración', 'Configuración',
                'setting', 'general', 'Configuración general'
            )
            """
        ),
        {"actor": current_user["id"]},
    )
    db.commit()
    return {"message": "Configuración guardada correctamente."}
