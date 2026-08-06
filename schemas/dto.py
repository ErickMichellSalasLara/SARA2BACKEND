from datetime import date, time
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from core.config import ALLOWED_EMAIL_DOMAIN

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_institutional_email(value: str) -> str:
    normalized = str(value).strip().lower()
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("Ingresa un correo electrónico válido.")
    if not normalized.endswith(ALLOWED_EMAIL_DOMAIN):
        raise ValueError(
            f"Solo se permiten correos institucionales {ALLOWED_EMAIL_DOMAIN}."
        )
    return normalized


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    remember: bool = False

    @field_validator("email")
    @classmethod
    def validate_domain(cls, value: str):
        return normalize_institutional_email(value)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    email: str
    password: str = Field(min_length=8, max_length=128)
    enrollment: str | None = Field(default=None, max_length=30)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str):
        return " ".join(value.split())

    @field_validator("email")
    @classmethod
    def validate_domain(cls, value: str):
        return normalize_institutional_email(value)


class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        return normalize_institutional_email(value)


class ReservationCreate(BaseModel):
    cubicle_id: int = Field(ge=1, le=4)
    user_id: int | None = Field(default=None, ge=1)
    reservation_date: date
    start_time: time
    end_time: time
    purpose: str | None = Field(default=None, max_length=250)
    number_of_people: int = Field(default=1, ge=1, le=8)


class LoanCreate(BaseModel):
    user_id: int = Field(ge=1)
    material_id: int = Field(ge=1)
    due_date: date


class AuditCreate(BaseModel):
    action: str = Field(min_length=2, max_length=100)
    module: str = Field(min_length=2, max_length=80)
    record: str | None = Field(default=None, max_length=200)


class UserCreate(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    email: str
    enrollment: str = Field(min_length=2, max_length=30)
    role: Literal["student", "admin"] = "student"
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str):
        return normalize_institutional_email(value)


class UserStatusUpdate(BaseModel):
    status: Literal["active", "inactive", "blocked", "pending"]


class SettingsUpdate(BaseModel):
    systemName: str = Field(min_length=2, max_length=100)
    serviceStart: time
    serviceEnd: time
    reservationDuration: int = Field(ge=15, le=480)
    tolerance: int = Field(ge=0, le=120)
    loanDays: int = Field(ge=1, le=60)
    allowedDomain: str = Field(min_length=4, max_length=100)
    emailNotifications: bool
    deniedAccessAlerts: bool
    overdueAlerts: bool
