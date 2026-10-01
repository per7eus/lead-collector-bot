import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

from aiogram import Bot
from yookassa import Configuration, Payment

from config import (
    YOOKASSA_SHOP_ID,
    YOOKASSA_SECRET_KEY,
    BOT_USERNAME,
    ADMIN_ID,
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

def get_current_price() -> int:
    """
    Возвращает актуальную стоимость
    по московскому времени.
    """

    now = datetime.now(MOSCOW)

    # До 20 сентября
    if now < datetime(
        2026,
        9,
        21,
        0,
        0,
        0,
        tzinfo=MOSCOW,
    ):
        return 3000

    # 21–30 сентября
    if now < datetime(
        2026,
        10,
        1,
        0,
        0,
        0,
        tzinfo=MOSCOW,
    ):
        return 4000

    # 1–10 октября
    if now <= datetime(
        2026,
        10,
        10,
        23,
        59,
        59,
        tzinfo=MOSCOW,
    ):
        return 5000

    # После мероприятия
    return 5000


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

        "📅 10 октября 2026\n"
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