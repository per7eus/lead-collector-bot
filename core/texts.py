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
# ШАБЛОНЫ ТЕКСТОВ
# =========================================================

START_TEXT = (
    "Привет 👋\n\n"
    "Я бот проекта Чёрного Кролика — эксперта по межполовым коммуникациям.\n\n"
    "Здесь ты можешь узнать подробности о мастер-классе «Пробуждение», "
    "зарегистрироваться и сразу оплатить участие.\n\n"
    "{price_schedule}\n\n"
    "Чем ближе мастер-класс, тем выше стоимость участия.\n\n"
    "После регистрации и оплаты я пришлю подтверждение и всю необходимую информацию.\n\n"
    "👇 Начнём с самого главного: что будет на мастер-классе и зачем тебе туда."
)

PROBLEM_TEXT = (
    "Можно сколько угодно изучать отношения, читать про знакомства и разбирать "
    "чужие истории. Но в момент, когда нужно самому проявить инициативу, начать "
    "разговор или сделать следующий шаг, теория часто заканчивается.\n\n"
    "«Пробуждение» — практический однодневный тренинг для мужчин и женщин, где мы "
    "разбираем, что мешает действовать в реальном взаимодействии с противоположным "
    "полом, и переносим это из разговоров в практику."
)

PROGRAM_TEXT = (
    "На «Пробуждении» мы последовательно пройдём путь от внутреннего напряжения "
    "до реального первого контакта.\n\n"
    "• страх, инициатива, эмоции и первый контакт;\n"
    "• снижение напряжения перед знакомством;\n"
    "• практическая часть и реальное взаимодействие;\n"
    "• разбор полученного опыта и ситуаций участников.\n\n"
    "Это не лекция на семь часов. Значительная часть тренинга посвящена практике."
)

FOR_WHOM_TEXT = (
    "Тренинг для мужчин и женщин 18+, которые хотят лучше понимать своё поведение "
    "во взаимодействии с противоположным полом и не оставаться только в теории.\n\n"
    "Подойдёт, если сложно проявлять инициативу, знакомиться, начинать общение, "
    "справляться с напряжением или переводить интерес в реальные действия."
)

EXPERT_TEXT = (
    "Чёрный Кролик — эксперт по межполовым коммуникациям.\n\n"
    "Более 10 лет обучает мужчин и женщин, проводит групповые и индивидуальные "
    "тренинги, полевую практику, интенсивы и мастер-классы. Проведено более 100 "
    "тренингов, обучение прошли более 1 000 человек."
)

CONDITIONS_TEXT = (
    "«Пробуждение»\n"
    "{event_date}\n"
    "Москва · м. Проспект Мира\n"
    "{event_time}\n"
    "Офлайн · 18+\n"
    "До 30 участников\n\n"
    "Точный адрес сообщит администратор после оплаты."
)

MENU_TEXT = (
    "Что тебя интересует?\n\n"
    "Выбери пункт ниже 👇"
)

ADMIN_PHONE = "+7 977 999 5655"
ADMIN_TG = "blackbrabbit"


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СБОРКИ ДАННЫХ
# =========================================================

def _load_db() -> dict:
    if not DB_PATH.exists():
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Ошибка при чтении %s: %s", DB_PATH, e)
        return {}


def get_price_schedule_block() -> str:
    """
    Генерирует блок цен в формате интервалов:
    🎟 Стоимость участия:
    с 18 по 28 октября — 3 000 ₽
    с 29 по 31 октября — 5 000 ₽
    """
    data = _load_db()
    tiers = data.get("tiers", [])

    if not tiers:
        default_price = data.get("default_price", 5000)
        formatted_default = f"{int(default_price):,}".replace(",", " ")
        return f"🎟 Стоимость участия:\n{formatted_default} ₽"

    # Сортируем интервалы по дате дедлайна
    sorted_tiers = sorted(tiers, key=lambda x: x.get("until", ""))

    # Парсим валидные дедлайны
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
        default_price = data.get("default_price", 5000)
        return f"🎟 Стоимость участия:\n{int(default_price):,} ₽".replace(",", " ")

    lines = ["🎟 Стоимость участия:"]

    prev_end_date = None

    for i, item in enumerate(parsed_tiers):
        dt_end = item["date"]
        price_str = f"{item['price']:,}".replace(",", " ")

        if i == 0:
            # Для первого периода берем условный старт (например, за 10 дней до дедлайна или начало месяца)
            # Если в первом периоде дата старта жестко не задана, выводим от 18 числа или старта продаж:
            start_day = 18 if dt_end.day >= 18 else 1
            start_month_str = MONTHS_RU.get(dt_end.month, "")
            end_month_str = MONTHS_RU.get(dt_end.month, "")

            if start_month_str == end_month_str:
                lines.append(f"с {start_day} по {dt_end.day} {end_month_str} — {price_str} ₽")
            else:
                lines.append(f"с {start_day} {start_month_str} по {dt_end.day} {end_month_str} — {price_str} ₽")
        else:
            # Следующий период начинается на следующий день после предыдущего дедлайна
            dt_start = prev_end_date + timedelta(days=1)
            start_month_str = MONTHS_RU.get(dt_start.month, "")
            end_month_str = MONTHS_RU.get(dt_end.month, "")

            # Если месяцы совпадают — пишем название месяца только в конце
            if dt_start.month == dt_end.month:
                lines.append(f"с {dt_start.day} по {dt_end.day} {end_month_str} — {price_str} ₽")
            else:
                lines.append(f"с {dt_start.day} {start_month_str} по {dt_end.day} {end_month_str} — {price_str} ₽")

        prev_end_date = dt_end

    return "\n".join(lines)

def get_event_info() -> tuple[str, str]:
    """Возвращает (event_date, event_time) из db.json."""
    data = _load_db()
    date_val = data.get("event_date", "Ошибка")
    time_val = data.get("event_time", "Ошибка")
    return date_val, time_val


# =========================================================
# ГОТОВЫЕ ФУНКЦИИ ДЛЯ ОТПРАВКИ СООБЩЕНИЙ ЧЕРЕЗ .format()
# =========================================================

def get_start_text() -> str:
    schedule = get_price_schedule_block()
    return START_TEXT.format(price_schedule=schedule)


def get_conditions_text() -> str:
    event_date, event_time = get_event_info()
    return CONDITIONS_TEXT.format(event_date=event_date, event_time=event_time)