from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.registration import Registration
from bot.keyboard.registration import phone_kb, age_kb, confirm_kb, edit_kb, remove_kb
from bot.core.validators import (
    is_valid_name, normalize_phone, parse_age, MIN_AGE,
)


router = Router()


DENY_TEXT = (
    "😔 К сожалению, участие доступно только с {min_age} лет.\n\n"
    "Если вы указали возраст ошибочно — нажмите /start и попробуйте снова."
)


# ---------- Старт ----------
@router.callback_query(F.data == "1.2")
async def start_registration(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("")
    await state.set_state(Registration.first_name)
    await call.message.answer(
        "Как я могу к вам обращаться? Напишите ваше *имя*.",
        parse_mode="Markdown",
    )


# ---------- Имя ----------
@router.message(Registration.first_name, F.text)
async def process_first_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not is_valid_name(name):
        await message.answer("Пожалуйста, введите корректное имя (только буквы, 2–50 символов).")
        return

    await state.update_data(first_name=name.title())
    await state.set_state(Registration.last_name)
    await message.answer(
        f"Приятно познакомиться, {name.title()}! Теперь напишите вашу *фамилию*.",
        parse_mode="Markdown",
    )


# ---------- Фамилия ----------
@router.message(Registration.last_name, F.text)
async def process_last_name(message: Message, state: FSMContext):
    surname = message.text.strip()
    if not is_valid_name(surname):
        await message.answer("Пожалуйста, введите корректную фамилию (только буквы, 2–50 символов).")
        return

    await state.update_data(last_name=surname.title())
    await state.set_state(Registration.age)
    await message.answer(
        "Сколько вам лет? Напишите число или выберите вариант ниже.",
        reply_markup=age_kb(),
    )


# ---------- Возраст ----------
@router.message(Registration.age, F.text)
async def process_age(message: Message, state: FSMContext):
    age = parse_age(message.text)

    if age is None:
        await message.answer(
            "Пожалуйста, укажите возраст числом (например, 25) "
            "или выберите один из вариантов."
        )
        return

    # ⛔ Отсекаем младше 18
    if age < MIN_AGE:
        await state.clear()
        await message.answer(
            DENY_TEXT.format(min_age=MIN_AGE),
            reply_markup=remove_kb,
        )
        return

    await state.update_data(age=age)
    await state.set_state(Registration.phone)
    await message.answer(
        "Отлично! Оставьте ваш *номер телефона* — нажмите кнопку ниже "
        "или введите вручную в формате +7XXXXXXXXXX.",
        parse_mode="Markdown",
        reply_markup=phone_kb(),
    )


# ---------- Телефон (контакт) ----------
@router.message(Registration.phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext):
    phone = normalize_phone(message.contact.phone_number)
    if not phone:
        await message.answer(
            "Не удалось распознать номер. Введите вручную в формате +7XXXXXXXXXX."
        )
        return

    await message.answer("📱 Номер получен", reply_markup=remove_kb)
    await _save_phone_and_show_summary(message, state, phone)


# ---------- Телефон (ручной ввод) ----------
@router.message(Registration.phone, F.text)
async def process_phone_text(message: Message, state: FSMContext):
    phone = normalize_phone(message.text)
    if not phone:
        await message.answer("Неверный формат. Пример: +79991234567")
        return

    await message.answer("📱 Номер сохранён", reply_markup=remove_kb)
    await _save_phone_and_show_summary(message, state, phone)


async def _save_phone_and_show_summary(message: Message, state: FSMContext, phone: str):
    await state.update_data(phone=phone)
    data = await state.get_data()
    await state.set_state(Registration.confirm)

    text = (
        "Проверьте, пожалуйста, данные:\n\n"
        f"👤 Имя: {data['first_name']}\n"
        f"👤 Фамилия: {data['last_name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"📞 Телефон: {data['phone']}\n\n"
        "Всё верно?"
    )
    await message.answer(text, reply_markup=confirm_kb())


# ---------- Изменить данные ----------
@router.callback_query(Registration.confirm, F.data == "reg_edit")
async def edit_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Что хотите изменить?", reply_markup=edit_kb())
    await callback.answer()


@router.callback_query(Registration.confirm, F.data == "reg_back")
async def back_to_summary(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = (
        "Проверьте, пожалуйста, данные:\n\n"
        f"👤 Имя: {data['first_name']}\n"
        f"👤 Фамилия: {data['last_name']}\n"
        f"🎂 Возраст: {data['age']}\n"
        f"📞 Телефон: {data['phone']}\n\n"
        "Всё верно?"
    )
    await callback.message.edit_text(text, reply_markup=confirm_kb())
    await callback.answer()


@router.callback_query(Registration.confirm, F.data == "edit_first_name")
async def edit_first_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.first_name)
    await callback.message.answer("Введите новое *имя*:", parse_mode="Markdown")
    await callback.answer()


@router.callback_query(Registration.confirm, F.data == "edit_last_name")
async def edit_last_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.last_name)
    await callback.message.answer("Введите новую *фамилию*:", parse_mode="Markdown")
    await callback.answer()


@router.callback_query(Registration.confirm, F.data == "edit_age")
async def edit_age(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.age)
    await callback.message.answer(
        "Введите новый возраст числом или выберите вариант:",
        reply_markup=age_kb(),
    )
    await callback.answer()


@router.callback_query(Registration.confirm, F.data == "edit_phone")
async def edit_phone(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.phone)
    await callback.message.answer(
        "Введите новый номер или нажмите кнопку ниже:",
        reply_markup=phone_kb(),
    )
    await callback.answer()