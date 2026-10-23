import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Путь к db/db.json от корня проекта
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent if (CURRENT_FILE.parent / "db").exists() else CURRENT_FILE.parent.parent
DB_PATH = PROJECT_ROOT / "db" / "db.json"

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЗАГРУЗКИ
# =========================================================

def _load_db() -> dict:
    if not DB_PATH.exists():
        logger.warning("Файл %s не найден", DB_PATH)
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Ошибка при чтении %s: %s", DB_PATH, e)
        return {}


def get_text_from_db(key: str, default: str = "") -> str:
    """Возвращает сырой шаблон текста по ключу из секции 'texts' в db.json."""
    data = _load_db()
    texts = data.get("texts", {})
    return texts.get(key, default)


def get_event_info() -> tuple[str, str]:
    """Возвращает (event_date, event_time) из db.json."""
    data = _load_db()
    date_val = data.get("event_date", "Дата уточняется")
    time_val = data.get("event_time", "Время уточняется")
    return date_val, time_val


def get_price_schedule_block() -> str:
    """
    Генерирует блок цен в формате интервалов:
    🎟 Стоимость участия:
    с 14 по 23 октября — 100 ₽
    ...
    """
    data = _load_db()
    tiers = data.get("tiers", [])

    if not tiers:
        default_price = data.get("default_price", 70000)
        formatted_default = f"{int(default_price):,}".replace(",", " ")
        return f"🎟 Стоимость участия:\n{formatted_default} ₽"

    # Сортируем интервалы по возрастанию даты дедлайна
    sorted_tiers = sorted(tiers, key=lambda x: x.get("until", ""))

    parsed_tiers = []
    for tier in sorted_tiers:
        until_raw = tier.get("until")
        price = tier.get("price")
        if not until_raw or price is None:
            continue
        try:
            dt = datetime.fromisoformat(until_raw.strip())
            parsed_tiers.append({"date": dt, "price": int(price)})
        except Exception:
            continue

    if not parsed_tiers:
        default_price = data.get("default_price", 70000)
        return f"🎟 Стоимость участия:\n{int(default_price):,} ₽".replace(",", " ")

    lines = ["🎟 Стоимость участия:"]
    prev_end_date = None

    for i, item in enumerate(parsed_tiers):
        dt_end = item["date"]
        price_str = f"{item['price']:,}".replace(",", " ")

        if i == 0:
            start_day = 18 if dt_end.day >= 18 else 1
            start_month_str = MONTHS_RU.get(dt_end.month, "")
            end_month_str = MONTHS_RU.get(dt_end.month, "")

            if start_month_str == end_month_str:
                lines.append(f"с {start_day} по {dt_end.day} {end_month_str} — {price_str} ₽")
            else:
                lines.append(f"с {start_day} {start_month_str} по {dt_end.day} {end_month_str} — {price_str} ₽")
        else:
            dt_start = prev_end_date + timedelta(days=1)
            start_month_str = MONTHS_RU.get(dt_start.month, "")
            end_month_str = MONTHS_RU.get(dt_end.month, "")

            if dt_start.month == dt_end.month:
                lines.append(f"с {dt_start.day} по {dt_end.day} {end_month_str} — {price_str} ₽")
            else:
                lines.append(f"с {dt_start.day} {start_month_str} по {dt_end.day} {end_month_str} — {price_str} ₽")

        prev_end_date = dt_end

    return "\n".join(lines)


# =========================================================
# ФУНКЦИИ ПОЛУЧЕНИЯ ГОТОВЫХ ТЕКСТОВ ДЛЯ БОТА
# =========================================================

def get_start_text() -> str:
    raw_template = get_text_from_db(
        "start",
        "Привет 👋\n\n{price_schedule}\n\n👇 Начнём с самого главного:"
    )
    schedule = get_price_schedule_block()
    return raw_template.format(price_schedule=schedule)


def get_conditions_text() -> str:
    raw_template = get_text_from_db(
        "conditions",
        "«Пробуждение»\n{event_date}\n{event_time}\nМосква"
    )
    event_date, event_time = get_event_info()
    return raw_template.format(event_date=event_date, event_time=event_time)


def get_problem_text() -> str:
    return get_text_from_db("problem")


def get_program_text() -> str:
    return get_text_from_db("program")


def get_for_whom_text() -> str:
    return get_text_from_db("for_whom")


def get_expert_text() -> str:
    return get_text_from_db("expert")


def get_menu_text() -> str:
    return get_text_from_db("menu", "Что тебя интересует?\n\nВыбери пункт ниже 👇")


def get_admin_contacts() -> tuple[str, str]:
    """Возвращает (phone, tg_username)."""
    phone = get_text_from_db("admin_phone", "+7 977 999 5655")
    tg = get_text_from_db("admin_tg", "blackbrabbit")
    return phone, tg