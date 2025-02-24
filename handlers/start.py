# handlers/start.py
import logging
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from models import User, Address
from db import async_session
from keyboards.reply import persistent_reply_keyboard
from utils.helpers import get_or_create_user, load_addresses, build_address_inline_keyboard
from handlers.form_states import Form  # Можна винести FSM стани в окремий файл
from loader import dp

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    logging.debug("Entered cmd_start handler")
    # Відправляємо постійну reply клавіатуру (наприклад, з кнопкою "Розпочати")
    await message.answer("Вітаємо! Натисніть кнопку \"/start\" для продовження.",
                         reply_markup=persistent_reply_keyboard())
    telegram_id = message.from_user.id
    user_name = (f"{message.from_user.first_name} {message.from_user.last_name}"
                 if message.from_user.last_name else message.from_user.first_name)
    try:
        user = await get_or_create_user(telegram_id, user_name)
        await state.update_data(user_id=user.id, telegram_id=telegram_id, user_name=user_name)
        addresses = await load_addresses(user.id)
        if addresses:
            text, inline_kb = build_address_inline_keyboard(addresses)
            await message.answer(text, reply_markup=inline_kb)
            await state.set_state(Form.address_confirm)
        else:
            await message.answer("Адреси не знайдено. Введіть адресу.\nВведіть місто:")
            await state.set_state(Form.city)
    except Exception as e:
        logging.exception("Error in cmd_start:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")
