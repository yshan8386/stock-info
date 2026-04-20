from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    AvailabilityRequest,
    AvailabilityResponse,
    LoginRequest,
    SignupRequest,
    UserOut,
)
from app.services.auth_service import create_access_token, create_user, get_user_by_username, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def set_auth_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.jwt_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    checks = [
        (User.username == payload.username, "DUPLICATE_USERNAME", "이미 사용 중인 아이디입니다"),
        (User.email == str(payload.email).lower(), "DUPLICATE_EMAIL", "이미 사용 중인 이메일입니다"),
        (User.phone == payload.phone, "DUPLICATE_PHONE", "이미 사용 중인 핸드폰 번호입니다"),
    ]
    for condition, code, message in checks:
        if db.scalar(select(User.id).where(condition)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": code, "message": message})

    user = create_user(db, payload)
    set_auth_cookie(response, create_access_token(user))
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = get_user_by_username(db, payload.username)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다")
    user.last_login_at = datetime.now()
    db.commit()
    set_auth_cookie(response, create_access_token(user))
    return AuthResponse(user=UserOut.model_validate(user))


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/check-username", response_model=AvailabilityResponse)
def check_username(payload: AvailabilityRequest, db: Session = Depends(get_db)) -> AvailabilityResponse:
    exists = db.scalar(select(User.id).where(User.username == payload.value))
    return AvailabilityResponse(available=exists is None)


@router.post("/check-email", response_model=AvailabilityResponse)
def check_email(payload: AvailabilityRequest, db: Session = Depends(get_db)) -> AvailabilityResponse:
    exists = db.scalar(select(User.id).where(User.email == payload.value.lower()))
    return AvailabilityResponse(available=exists is None)


@router.post("/check-phone", response_model=AvailabilityResponse)
def check_phone(payload: AvailabilityRequest, db: Session = Depends(get_db)) -> AvailabilityResponse:
    phone = "".join(ch for ch in payload.value if ch.isdigit())
    exists = db.scalar(select(User.id).where(User.phone == phone))
    return AvailabilityResponse(available=exists is None)

