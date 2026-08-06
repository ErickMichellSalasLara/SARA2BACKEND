from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import ALLOWED_EMAIL_DOMAIN
from core.security import create_access_token, hash_password, verify_password
from database import get_db
from dependencies import get_current_user
from schemas.dto import ForgotPasswordRequest, LoginRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _public_user(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "enrollment": row.get("enrollment"),
        "role": row["role"],
    }


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    row = db.execute(
        text(
            """
            SELECT
                u.id,
                u.full_name AS name,
                u.email,
                u.enrollment,
                u.password_hash,
                u.status,
                r.code AS role
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.email = :email
            LIMIT 1
            """
        ),
        {"email": email},
    ).mappings().first()

    if not row or row["status"] != "active" or not verify_password(
        payload.password, row["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
        )

    token = create_access_token(row["id"], row["role"], row["email"])

    db.execute(
        text("UPDATE users SET last_login_at = NOW() WHERE id = :user_id"),
        {"user_id": row["id"]},
    )
    db.execute(
        text(
            """
            INSERT INTO audit_logs (
                actor_user_id, action, module, entity_type, entity_id,
                record_label, ip_address, user_agent
            ) VALUES (
                :actor_user_id, 'Inició sesión', 'Autenticación', 'user',
                :entity_id, :record_label, :ip_address, :user_agent
            )
            """
        ),
        {
            "actor_user_id": row["id"],
            "entity_id": str(row["id"]),
            "record_label": row["email"],
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", "")[:500],
        },
    )
    db.commit()

    return {
        "token": token,
        "token_type": "bearer",
        "user": _public_user(dict(row)),
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if not email.endswith(ALLOWED_EMAIL_DOMAIN):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Solo se permiten correos institucionales {ALLOWED_EMAIL_DOMAIN}.",
        )

    enrollment = (payload.enrollment or f"UTR-{secrets.token_hex(4)}").strip().upper()
    role_id = db.execute(
        text("SELECT id FROM roles WHERE code = 'student' LIMIT 1")
    ).scalar_one_or_none()
    if role_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La base de datos no contiene el rol student.",
        )

    try:
        result = db.execute(
            text(
                """
                INSERT INTO users (
                    full_name, email, enrollment, password_hash, role_id,
                    status, email_verified_at
                ) VALUES (
                    :name, :email, :enrollment, :password_hash, :role_id,
                    'active', NOW()
                )
                """
            ),
            {
                "name": payload.name,
                "email": email,
                "enrollment": enrollment,
                "password_hash": hash_password(payload.password),
                "role_id": role_id,
            },
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo o la matrícula ya están registrados.",
        ) from exc

    return {
        "message": "Cuenta creada correctamente.",
        "user_id": result.lastrowid,
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"user": _public_user(current_user)}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()
    user_id = db.execute(
        text("SELECT id FROM users WHERE email = :email AND status = 'active' LIMIT 1"),
        {"email": email},
    ).scalar_one_or_none()

    # Always return the same response so the endpoint does not reveal registered emails.
    if user_id is not None:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now() + timedelta(minutes=30)
        db.execute(
            text(
                """
                INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
                VALUES (:user_id, :token_hash, :expires_at)
                """
            ),
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
            },
        )
        db.commit()

    return {
        "message": (
            "Si el correo está registrado, se generaron instrucciones de recuperación. "
            "El envío de correo debe configurarse con un proveedor SMTP."
        )
    }
