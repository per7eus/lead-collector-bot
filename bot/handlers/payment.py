import logging
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from core.payment import (
    ORDERS,
    create_order_id,
    create_yookassa_payment,
    get_current_price,
    start_payment_monitor,
)
from core.texts import get_event_info
from bot.states.registration import Registration
from config import ADMIN_ID

logger = logging.getLogger(__name__)

router = Router()


# =========================================================
# ПЕРЕХОД К ОПЛАТЕ
# =========================================================

@router.callback_query(
    Registration.confirm,
    F.data == "reg_confirm",
)
async def confirm_registration(
    callback: CallbackQuery,
    bot: Bot,
    state: FSMContext,
):
    data = await state.get_data()

    telegram_id = callback.from_user.id
    first_name = data.get("first_name", "")
    last_name = data.get("last_name", "")
    phone = data.get("phone", "")
    source = data.get("source")

    # =====================================================
    # ЦЕНА И ДАННЫЕ МЕРОПРИЯТИЯ
    # =====================================================

    amount = get_current_price()
    event_date, event_time = get_event_info()

    # =====================================================
    # ORDER ID
    # =====================================================

    order_id = create_order_id(telegram_id)

    # =====================================================
    # СОЗДАЁМ ПЛАТЁЖ
    # =====================================================

    try:
        payment = create_yookassa_payment(
            order_id=order_id,
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            source=source,
            amount=amount,
        )
    except Exception as e:
        logger.exception("Ошибка создания платежа ЮKassa: %s", e)

        await callback.message.answer(
            "Не удалось создать платёж.\n\n"
            "Попробуй ещё раз через несколько секунд."
        )
        await callback.answer()
        return

    # =====================================================
    # СОХРАНЯЕМ ЗАКАЗ
    # =====================================================

    ORDERS[order_id] = {
        "telegram_id": telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "source": source,
        "amount": amount,
        "payment_id": payment.id,
        "status": "payment_pending",
        "paid_at": None,
    }

    # =====================================================
    # URL ОПЛАТЫ
    # =====================================================

    payment_url = payment.confirmation.confirmation_url

    # =====================================================
    # КНОПКА
    # =====================================================

    formatted_amount = f"{amount:,}".replace(",", " ")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💳 Оплатить {formatted_amount} ₽",
                    url=payment_url,
                )
            ]
        ]
    )

    # =====================================================
    # УДАЛЯЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ
    # =====================================================

    await callback.message.delete()

    # =====================================================
    # ОТПРАВЛЯЕМ ОПЛАТУ
    # =====================================================

    await callback.message.answer(
        "💳 Оплата участия\n\n"
        "Мастер-класс «Пробуждение»\n\n"
        f"📅 {event_date}\n"
        f"🕒 Время: {event_time}\n"
        "📍 Москва, м. Проспект Мира\n\n"
        f"Стоимость участия: {formatted_amount} ₽\n\n"
        "Нажми кнопку ниже, чтобы перейти к оплате ЮKassa.\n\n"
        "После оплаты бот автоматически проверит статус платежа.",
        reply_markup=keyboard,
    )

    # =====================================================
    # АДМИНУ
    # =====================================================

    username_part = f"@{callback.from_user.username}" if callback.from_user.username else "нет username"

    await bot.send_message(
        ADMIN_ID,
        "📝 Создана заявка на оплату (Пока не оплачено)\n\n"
        f"Имя: {first_name}\n"
        f"Фамилия: {last_name}\n"
        f"Телефон: {phone}\n\n"
        f"Telegram ID: {telegram_id}\n"
        f"Username: {username_part}\n\n"
        f"Сумма: {formatted_amount} ₽\n"
        f"Order ID: {order_id}\n"
        f"Payment ID: {payment.id}"
    )

    # =====================================================
    # ЗАПУСКАЕМ ПРОВЕРКУ
    # =====================================================

    start_payment_monitor(
        bot,
        order_id,
    )

    # =====================================================
    # ОЧИЩАЕМ FSM
    # =====================================================

    await state.clear()
    await callback.answer()


# =========================================================
# ВОЗВРАТ ПОЛЬЗОВАТЕЛЯ ИЗ ЮKASSA
# =========================================================

@router.message(
    F.text.startswith("/start payment_")
)
async def payment_return(
    message: Message,
    bot: Bot,
):
    # Извлекаем order_id целиком (он уже содержит "reg_")
    order_id = message.text.replace("/start payment_", "", 1).strip()

    order = ORDERS.get(order_id)

    if not order:
        await message.answer(
            "Не удалось найти платёж.\n\n"
            "Если ты уже оплатил(а), свяжись с администратором."
        )
        return

    if order["status"] == "paid":
        await message.answer(
            "Оплата уже подтверждена ✅"
        )
        return

    start_payment_monitor(
        bot,
        order_id,
    )

    await message.answer(
        "Проверяю оплату... ⏳\n\n"
        "Обычно подтверждение занимает несколько секунд."
    )

