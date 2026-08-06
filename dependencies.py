from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.security import TokenError, decode_access_token
from database import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debes iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (TokenError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc) or "Sesión inválida.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    row = db.execute(
        text(
            """
            SELECT
                u.id,
                u.full_name AS name,
                u.email,
                u.enrollment,
                u.status,
                r.code AS role
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.id = :user_id
            LIMIT 1
            """
        ),
        {"user_id": user_id},
    ).mappings().first()

    if not row or row["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta no existe o no está activa.",
        )

    return dict(row)


def require_roles(*allowed_roles: str) -> Callable:
    normalized_roles = {role.strip().lower() for role in allowed_roles}

    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if str(current_user.get("role", "")).lower() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para realizar esta acción.",
            )
        return current_user

    return dependency


require_admin = require_roles("admin")
require_staff = require_roles("admin", "librarian")
