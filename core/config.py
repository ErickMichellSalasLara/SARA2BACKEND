import os


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


APP_NAME = os.getenv("APP_NAME", "S.A.R.A. Backend")
API_PREFIX = os.getenv("API_PREFIX", "/api")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()

_DEFAULT_JWT_SECRET = "change-this-secret-in-production"
JWT_SECRET = os.getenv("JWT_SECRET", _DEFAULT_JWT_SECRET)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "120"))
ALLOWED_EMAIL_DOMAIN = os.getenv("ALLOWED_EMAIL_DOMAIN", "@utr.edu.mx").lower()
DATABASE_TIMEZONE = os.getenv("DATABASE_TIMEZONE", "-06:00")

if ENVIRONMENT == "production" and JWT_SECRET == _DEFAULT_JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET debe configurarse con una clave segura antes de ejecutar en producción."
    )

CORS_ORIGINS = _split_csv(
    os.getenv(
        "CORS_ORIGINS",
        "https://sara2-production.up.railway.app",
    )
)
