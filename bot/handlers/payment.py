from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)

from bot.states.registration import Registration

from config import ADMIN_ID

from bot.core.payment import (
    ORDERS,
    create_order_id,
    create_yookassa_payment,
    get_current_price,
    start_payment_monitor,
)


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

    first_name = data.get(
        "first_name",
        "",
    )

    last_name = data.get(
        "last_name",
        "",
    )

    phone = data.get(
        "phone",
        "",
    )

    source = data.get(
        "source",
    )

    # =====================================================
    # ЦЕНА
    # =====================================================

    amount = get_current_price()

    # =====================================================
    # TODO:
    #
    # Здесь позже добавим БД и проверку:
    #
    # if оплаченных >= 30:
    #     ...
    #
    # =====================================================

    # =====================================================
    # ORDER ID
    # =====================================================

    order_id = create_order_id(
        telegram_id
    )

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

        print(
            "Ошибка создания платежа ЮKassa:",
            e,
        )

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

    payment_url = (
        payment
        .confirmation
        .confirmation_url
    )

    # =====================================================
    # КНОПКА
    # =====================================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        f"💳 Оплатить "
                        f"{amount} ₽"
                    ),
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

        "Мастер-класс "
        "«Пробуждение»\n\n"

        "📅 10 октября 2026\n"
        "🕒 Начало в 15:00\n"
        "📍 Москва, м. Проспект Мира\n\n"

        f"Стоимость участия: "
        f"{amount} ₽\n\n"

        "Нажми кнопку ниже, чтобы "
        "перейти к оплате ЮKassa.\n\n"

        "После оплаты бот автоматически "
        "проверит статус платежа.",

        reply_markup=keyboard,
    )

    # =====================================================
    # АДМИНУ
    # =====================================================

    await bot.send_message(

        ADMIN_ID,

        "📝 Создана заявка на оплату (Пока не оплачено)\n\n"

        f"Имя: {first_name}\n"
        f"Фамилия: {last_name}\n"
        f"Телефон: {phone}\n\n"

        f"Telegram ID: {telegram_id}\n"
        f"Username: @{callback.from_user.username}\n\n"

        f"Сумма: {amount} ₽\n"
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
#
# ЮKassa возвращает пользователя примерно сюда:
#
# https://t.me/YOUR_BOT?start=payment_reg_...
#
# =========================================================

@router.message(
    F.text.startswith("/start payment_")
)
async def payment_return(
    message: Message,
    bot: Bot,
):

    payload = (
        message.text
        .replace(
            "/start payment_",
            "",
            1,
        )
        .strip()
    )

    order_id = (
        f"reg_{payload}"
    )

    order = ORDERS.get(
        order_id
    )

    if not order:

        await message.answer(
            "Не удалось найти платёж.\n\n"
            "Если ты уже оплатил(а), "
            "свяжись с администратором."
        )

        return

    if order["status"] == "paid":

        await message.answer(
            "Оплата уже подтверждена ✅"
        )

        return

    # Мониторинг уже мог быть запущен.
    #
    # Запускаем ещё один безопасно:
    # finish_payment() проверяет status=paid,
    # поэтому повторно сообщение не уйдёт.
    start_payment_monitor(
        bot,
        order_id,
    )

    await message.answer(
        "Проверяю оплату... ⏳\n\n"
        "Обычно подтверждение занимает "
        "несколько секунд."
    )