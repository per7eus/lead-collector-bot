import re

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё\-\s]{2,50}$")
PHONE_RE = re.compile(r"^\+?\d{10,15}$")

MIN_AGE = 18
MAX_AGE = 100


def is_valid_name(value: str) -> bool:
    return bool(NAME_RE.fullmatch(value.strip()))


def normalize_phone(value: str) -> str | None:
    cleaned = re.sub(r"[^\d+]", "", value)
    if cleaned.startswith("8") and len(cleaned) == 11:
        cleaned = "+7" + cleaned[1:]
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned if PHONE_RE.fullmatch(cleaned) else None


def parse_age(value: str) -> int | None:
    """Число 14–100 или диапазон из age_kb. Возвращает int или None."""
    value = value.strip()

    if value.isdigit():
        age = int(value)
        return age if 14 <= age <= MAX_AGE else None

    mapping = {
        "До 18": 17,
        "18–25": 22,
        "26–35": 30,
        "36–50": 43,
        "50+": 55,
    }
    return mapping.get(value)