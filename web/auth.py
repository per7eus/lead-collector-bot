import secrets
from typing import Optional
from pydantic import BaseModel
from fastapi import Header, HTTPException, status

from config import ADMIN_USERNAME, ADMIN_PASSWORD

# Хранилище активных токенов (в памяти: token -> username)
active_sessions: dict[str, str] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


def authenticate_user(data: LoginRequest) -> str:
    """Проверяет логин/пароль и создает сессионный токен."""
    valid_user = secrets.compare_digest(data.username, ADMIN_USERNAME)
    valid_pass = secrets.compare_digest(data.password, ADMIN_PASSWORD)

    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )

    token = secrets.token_hex(32)
    active_sessions[token] = data.username
    return token


def get_current_admin(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI Dependency для защиты админских эндпоинтов."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен авторизации отсутствует"
        )

    token = authorization.replace("Bearer ", "").strip()
    username = active_sessions.get(token)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия недействительна или истекла"
        )

    return username