import json
import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo
from pathlib import Path

from aiogram import Bot
from yookassa import Configuration, Payment

from config import (
    ADMIN_ID,
    BOT_USERNAME,
    YOOKASSA_SECRET_KEY,
    YOOKASSA_SHOP_ID,
)

logger = logging.getLogger(__name__)


# =========================================================
# YOOKASSA CONFIG
# =========================================================

Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY


MOSCOW = ZoneInfo("Europe/Moscow")


# =========================================================
# ВРЕМЕННОЕ ХРАНИЛИЩЕ ПЛАТЕЖЕЙ
# =========================================================
#
# Для первого запуска этого достаточно.
#
# В production потом лучше заменить на SQLite/PostgreSQL.
#
# order_id -> данные заказа
#

ORDERS = {}


# =========================================================
# ЦЕНА
# =========================================================
# Путь к db.json относительно текущего файла
CURRENT_FILE = Path(__file__).resolve()

# Поднимаемся на уровень выше: из core/ в корень проекта lead-collector-bot/
PROJECT_ROOT = CURRENT_FILE.parent.parent

# Итоговый абсолютный путь к db.json
DB_PATH = PROJECT_ROOT / "db" / "db.json"


def get_current_price() -> int:
    """
    Возвращает актуальную стоимость по московскому времени,
    считывая настроенные периоды из db/db.json.
    """
    fallback_price = 10000000000000000

    if not DB_PATH.exists():
        logger.warning("Файл базы %s не найден, возвращаем fallback: %d", DB_PATH, fallback_price)
        return fallback_price

    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.exception("Ошибка чтения %s: %s. Возвращаем fallback: %d", DB_PATH, e, fallback_price)
        return fallback_price

    default_price = data.get("default_price", fallback_price)
    tiers = data.get("tiers", [])

    if not tiers:
        return default_price

    now = datetime.now(MOSCOW)

    # Проходим по периодам
    for tier in tiers:
        until_raw = tier.get("until")
        price = tier.get("price")

        if not until_raw or price is None:
            continue

        try:
            # Нормализуем ISO-строку (например, "2026-10-28 23:59:59")
            dt_until = datetime.fromisoformat(until_raw.strip())

            # Привязываем к часовому поясу Москвы, если дата наивная
            if dt_until.tzinfo is None:
                dt_until = dt_until.replace(tzinfo=MOSCOW)

            # Если текущее время еще не превысило дедлайн периода
            if now <= dt_until:
                return int(price)

        except (ValueError, TypeError) as err:
            logger.error("Неверный формат даты в tier (id=%s): %s", tier.get("id"), err)
            continue

    # Если все дедлайны уже позади
    return int(default_price)

# =========================================================
# СОЗДАНИЕ ORDER ID
# =========================================================

def create_order_id(
    telegram_id: int,
) -> str:

    return (
        f"reg_{telegram_id}_"
        f"{uuid4().hex[:10]}"
    )


# =========================================================
# СОЗДАНИЕ ПЛАТЕЖА
# =========================================================

def create_yookassa_payment(
    *,
    order_id: str,
    telegram_id: int,
    first_name: str,
    last_name: str,
    phone: str,
    source: str | None,
    amount: int,
):
    """
    Создаёт платёж в ЮKassa.
    """

    idempotence_key = str(
        uuid4()
    )

    payment = Payment.create(
        {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB",
            },

            # Одностадийный платёж
            "capture": True,

            "confirmation": {
                "type": "redirect",

                # После оплаты ЮKassa может
                # вернуть пользователя в Telegram.
                #
                # Это НЕ webhook.
                #
                "return_url": (
                    f"https://t.me/"
                    f"{BOT_USERNAME}"
                    f"?start=payment_{order_id}"
                ),
            },

            "description": (
                "Участие в мастер-классе "
                "«Пробуждение», 10.10.2026"
            ),

            "metadata": {
                "internal_order_id": order_id,
                "telegram_id": str(
                    telegram_id
                ),
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "source": source or "",
            },
        },
        idempotence_key,
    )

    return payment


# =========================================================
# ПРОВЕРКА ПЛАТЕЖА
# =========================================================

def check_payment(
    payment_id: str,
):
    """
    Получает актуальное состояние платежа
    напрямую через API ЮKassa.
    """

    return Payment.find_one(
        payment_id
    )


# =========================================================
# ЗАВЕРШЕНИЕ ПЛАТЕЖА
# =========================================================

async def finish_payment(
    bot: Bot,
    order_id: str,
    payment
):
    """
    Вызывается только после подтверждения
    успешного платежа.
    """

    order = ORDERS.get(
        order_id
    )

    if not order:
        logger.error(
            "Заказ не найден: %s",
            order_id,
        )
        return

    # -----------------------------------------------------
    # Идемпотентность
    # -----------------------------------------------------

    if order["status"] == "paid":
        return

    # -----------------------------------------------------
    # Проверяем сумму
    # -----------------------------------------------------

    expected_amount = Decimal(
        str(order["amount"])
    )

    actual_amount = Decimal(
        payment.amount.value
    )

    if actual_amount != expected_amount:

        logger.error(
            "НЕСООТВЕТСТВИЕ СУММЫ: "
            "order=%s expected=%s actual=%s",
            order_id,
            expected_amount,
            actual_amount,
        )

        return

    # -----------------------------------------------------
    # Проверяем валюту
    # -----------------------------------------------------

    if payment.amount.currency != "RUB":

        logger.error(
            "Неверная валюта платежа: %s",
            payment.amount.currency,
        )

        return

    # -----------------------------------------------------
    # Проверяем статус
    # -----------------------------------------------------

    if payment.status != "succeeded":
        return

    if not payment.paid:
        return

    # -----------------------------------------------------
    # Ставим paid
    # -----------------------------------------------------

    order["status"] = "paid"

    order["paid_at"] = datetime.now(
        MOSCOW
    )

    order["payment_id"] = payment.id

    logger.info(
        "ОПЛАТА ПОДТВЕРЖДЕНА: %s",
        order_id,
    )

    telegram_id = order[
        "telegram_id"
    ]

    # -----------------------------------------------------
    # Сообщение пользователю
    # -----------------------------------------------------

    await bot.send_message(
        telegram_id,

        "Оплата прошла ✅\n\n"

        "Ты зарегистрирован(а) "
        "на мастер-класс «Пробуждение».\n\n"

        "📅 31 октября 2026\n"
        "🕒 Начало в 15:00\n"
        "📍 Москва, м. Проспект Мира\n\n"

        "Точный адрес сообщит "
        "администратор проекта.\n\n"

        "Статус: оплачено."
    )

    # -----------------------------------------------------
    # Сообщение админу
    # -----------------------------------------------------

    await bot.send_message(
        ADMIN_ID,

        "💰 ОПЛАТА ПОЛУЧЕНА\n\n"

        f"Имя: {order['first_name']}\n"
        f"Фамилия: {order['last_name']}\n"
        f"Телефон: {order['phone']}\n\n"

        f"Telegram ID: {telegram_id}\n"
        f"Сумма: {order['amount']} ₽\n"

        f"Order ID: {order_id}\n"
        f"Payment ID: {payment.id}"
    )


# =========================================================
# МОНИТОРИНГ ПЛАТЕЖА
# =========================================================

async def monitor_payment(
    bot: Bot,
    order_id: str,
):
    """
    Проверяет платёж каждые 5 секунд.

    Максимальное время ожидания:
    30 минут.
    """

    logger.info(
        "Начинаем мониторинг платежа: %s",
        order_id,
    )

    # 30 минут / 5 секунд
    max_attempts = 360

    for _ in range(max_attempts):

        await asyncio.sleep(5)

        order = ORDERS.get(
            order_id
        )

        if not order:
            return

        # Уже оплачено
        if order["status"] == "paid":
            return

        payment_id = order.get(
            "payment_id"
        )

        if not payment_id:
            return

        try:

            payment = check_payment(
                payment_id
            )

        except Exception as e:

            logger.exception(
                "Ошибка проверки платежа %s: %s",
                payment_id,
                e,
            )

            # Не падаем.
            # Следующая попытка через 5 секунд.
            continue

        # -------------------------------------------------
        # Успешно
        # -------------------------------------------------

        if (
            payment.status == "succeeded"
            and payment.paid
        ):

            await finish_payment(
                bot,
                order_id,
                payment,
            )

            return

        # -------------------------------------------------
        # Отмена
        # -------------------------------------------------

        if payment.status == "canceled":

            order["status"] = (
                "payment_canceled"
            )

            logger.info(
                "Платёж отменён: %s",
                order_id,
            )

            return

    # -----------------------------------------------------
    # Время ожидания закончилось
    # -----------------------------------------------------

    order = ORDERS.get(
        order_id
    )

    if order and order["status"] != "paid":

        order["status"] = (
            "payment_timeout"
        )

        logger.info(
            "Истёк срок ожидания платежа: %s",
            order_id,
        )


# =========================================================
# ЗАПУСК МОНИТОРИНГА
# =========================================================

def start_payment_monitor(
    bot: Bot,
    order_id: str,
):
    """
    Запускает фоновую проверку платежа.
    """

    asyncio.create_task(
        monitor_payment(
            bot,
            order_id,
        )
    )