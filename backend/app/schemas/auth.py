from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SignupRequest(BaseModel):
    username: str = Field(pattern=r"^[a-zA-Z0-9_]{4,20}$")
    password: str = Field(min_length=8)
    password_confirm: str = Field(min_length=8)
    display_name: str = Field(min_length=2, max_length=20)
    phone: str
    email: EmailStr

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) not in (10, 11):
            raise ValueError("phone must be 10 or 11 digits")
        return digits

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password_confirm")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        if info.data.get("password") and value != info.data["password"]:
            raise ValueError("passwords do not match")
        return value


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    user: UserOut


class AvailabilityRequest(BaseModel):
    value: str


class AvailabilityResponse(BaseModel):
    available: bool

