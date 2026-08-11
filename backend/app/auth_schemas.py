import re

from pydantic import BaseModel, EmailStr, field_validator

PHONE_RE = re.compile(r"^(\+216)?\d{8}$")


class SimpleRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone: str
    role: str
    address: str = "Tunis"  # Default address

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str) -> str:
        cleaned = v.replace(" ", "")
        if not PHONE_RE.match(cleaned):
            raise ValueError("Phone must be 8 digits, optionally prefixed with +216")
        return cleaned

    @field_validator("role")
    @classmethod
    def role_must_be_worker_or_client(cls, v: str) -> str:
        if v not in ("worker", "client"):
            raise ValueError("Role must be 'worker' or 'client'")
        return v
