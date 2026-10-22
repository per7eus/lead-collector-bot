import json
import os
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from web.auth import LoginRequest, authenticate_user, get_current_admin

router = APIRouter()

# ---------------------------------------------------------
# Пути к файлам и шаблонам
# ---------------------------------------------------------
CURRENT_FILE = Path(__file__).resolve()
# web/ -> корень проекта lead-collector-bot/
PROJECT_ROOT = CURRENT_FILE.parent.parent
DB_PATH = PROJECT_ROOT / "db" / "db.json"
TEMPLATES_DIR = CURRENT_FILE.parent / "templates"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ---------------------------------------------------------
# Модели Pydantic
# ---------------------------------------------------------
class TierCreateRequest(BaseModel):
    until: str = Field(..., description="Дедлайн интервала, например '2026-10-28 23:59:59'")
    price: int = Field(..., ge=0, description="Стоимость участия")


class DefaultPriceRequest(BaseModel):
    default_price: int = Field(..., ge=0, description="Базовая стоимость после дедлайнов")


class EventInfoRequest(BaseModel):
    event_date: str = Field(..., description="Дата мероприятия, например '31 октября 2026'")
    event_time: str = Field(..., description="Время проведения, например '15:00–22:00/22:30'")


# ---------------------------------------------------------
# Атомарная работа с JSON через буфер-файл
# ---------------------------------------------------------
def load_db() -> Dict[str, Any]:
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        default_data = {
            "event_date": "31 октября 2026",
            "event_time": "15:00–22:00/22:30",
            "default_price": 5000,
            "tiers": []
        }
        save_db(default_data)
        return default_data

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {
            "event_date": "31 октября 2026",
            "event_time": "15:00–22:00/22:30",
            "default_price": 5000,
            "tiers": []
        }


def save_db(data: Dict[str, Any]) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = DB_PATH.with_suffix(".tmp")

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(temp_path, DB_PATH)


# ---------------------------------------------------------
# Эндпоинты авторизации и страницы
# ---------------------------------------------------------
@router.get("/admin", response_class=HTMLResponse)
async def serve_admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html")


@router.post("/api/admin/login")
async def login(data: LoginRequest):
    token = authenticate_user(data)
    return {"token": token, "username": data.username}


@router.get("/api/admin/check")
async def check_admin(current_user: str = Depends(get_current_admin)):
    return {"status": "ok", "user": current_user}


# ---------------------------------------------------------
# Эндпоинты цен и настроек мероприятия
# ---------------------------------------------------------
@router.get("/api/admin/prices")
async def get_prices(current_user: str = Depends(get_current_admin)):
    return load_db()


@router.post("/api/admin/event")
async def update_event_info(
    data: EventInfoRequest,
    current_user: str = Depends(get_current_admin),
):
    db_data = load_db()
    db_data["event_date"] = data.event_date.strip()
    db_data["event_time"] = data.event_time.strip()
    save_db(db_data)

    return {
        "status": "ok",
        "event_date": db_data["event_date"],
        "event_time": db_data["event_time"]
    }


@router.post("/api/admin/prices/tier")
async def add_price_tier(
    tier: TierCreateRequest,
    current_user: str = Depends(get_current_admin),
):
    db_data = load_db()
    tiers: List[Dict[str, Any]] = db_data.get("tiers", [])

    new_id = max([t.get("id", 0) for t in tiers], default=0) + 1

    until_formatted = tier.until.replace("T", " ")
    if len(until_formatted) == 16:
        until_formatted += ":00"

    new_tier = {
        "id": new_id,
        "until": until_formatted,
        "price": tier.price,
    }

    tiers.append(new_tier)
    tiers.sort(key=lambda x: x["until"])

    db_data["tiers"] = tiers
    save_db(db_data)

    return {"status": "ok", "tier": new_tier}


@router.delete("/api/admin/prices/tier/{tier_id}")
async def delete_price_tier(
    tier_id: int,
    current_user: str = Depends(get_current_admin),
):
    db_data = load_db()
    tiers = db_data.get("tiers", [])

    initial_len = len(tiers)
    tiers = [t for t in tiers if t.get("id") != tier_id]

    if len(tiers) == initial_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Период с таким ID не найден",
        )

    db_data["tiers"] = tiers
    save_db(db_data)

    return {"status": "ok", "deleted_id": tier_id}


@router.post("/api/admin/prices/default")
async def update_default_price(
    data: DefaultPriceRequest,
    current_user: str = Depends(get_current_admin),
):
    db_data = load_db()
    db_data["default_price"] = data.default_price
    save_db(db_data)

    return {"status": "ok", "default_price": data.default_price}