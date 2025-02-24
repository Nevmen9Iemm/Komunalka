import logging
from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from models import Address
from db import async_session
from keyboards.inline import menu_keyboards
from handlers.form_states import Form
from loader import dp

@dp.callback_query(F.data.startswith("select_address_"))
async def process_select_address(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_select_address handler")
    try:
        current_state = await state.get_state()
        if current_state != Form.address_confirm.state:
            return
        # Отримуємо id адреси із callback data
        addr_id = int(callback.data.split("_")[-1])
        await state.update_data(address_id=addr_id)
        await callback.answer()  # повідомлення про успішну обробку callback

        # Завантажуємо дані адреси з бази даних
        async with async_session() as session:
            stmt = select(Address).where(Address.id == addr_id)
            result = await session.execute(stmt)
            address = result.scalars().first()
            if address:
                full_address = f"{address.city}, {address.street}, {address.house}"
                if address.apartment:
                    full_address += f", кв. {address.apartment}"
            else:
                full_address = "невідома адреса"

        data = await state.get_data()
        address_id = data.get("address_id")
        user_id = data.get("user_id")

        # Формуємо inline клавіатуру для вибору послуг
        await callback.message.edit_text(
            f"Оберіть комунальну послугу для адреси {full_address}:",
            reply_markup=menu_keyboards(address_id=address_id, user_id=user_id)
        )
        await state.set_state(Form.service)
    except Exception as e:
        logging.exception("Помилка у process_select_address:")
        await callback.message.edit_text(
            "Сталася помилка. Спробуйте пізніше. Натисніть кнопку \"/start\" для продовження",
            reply_markup=None
        )

@dp.callback_query(lambda c: c.data == "add_new_address")
async def process_add_new_address(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_add_new_address handler")
    try:
        await callback.answer()
        await callback.message.edit_text(
            "Введіть назву міста:",
            reply_markup=None
        )
        await state.set_state(Form.city)
    except Exception as e:
        logging.exception("Помилка у process_add_new_address:")
        await callback.message.edit_text(
            "Сталася помилка. Спробуйте пізніше. Натисніть кнопку \"/start\" для продовження",
            reply_markup=None
        )


@dp.message(F.text, StateFilter(Form.city))
async def process_city(message: types.Message, state: FSMContext):
    logging.debug("Entered process_city handler")
    try:
        await state.update_data(city=message.text.strip())
        await message.answer("Введіть вулицю:")
        await state.set_state(Form.street)
    except Exception as e:
        logging.error(f"Помилка у process_city: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.street))
async def process_street(message: types.Message, state: FSMContext):
    logging.debug("Entered process_street handler")
    try:
        await state.update_data(street=message.text.strip())
        await message.answer("Введіть номер будинку:")
        await state.set_state(Form.house)
    except Exception as e:
        logging.error(f"Помилка у process_street: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.house))
async def process_house(message: types.Message, state: FSMContext):
    logging.debug("Entered process_house handler")
    try:
        await state.update_data(house=message.text.strip())
        await message.answer("Введіть під'їзд (якщо є, інакше введіть '-' ):")
        await state.set_state(Form.entrance)
    except Exception as e:
        logging.error(f"Помилка у process_house: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.entrance))
async def process_entrance(message: types.Message, state: FSMContext):
    logging.debug("Entered process_entrance handler")
    try:
        entrance = message.text.strip()
        if entrance == "-":
            entrance = None
        await state.update_data(entrance=entrance)
        await message.answer("Введіть поверх (якщо є, інакше введіть '-' ):")
        await state.set_state(Form.floor)
    except Exception as e:
        logging.error(f"Помилка у process_entrance: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.floor))
async def process_floor(message: types.Message, state: FSMContext):
    logging.debug("Entered process_floor handler")
    try:
        floor = message.text.strip()
        if floor == "-":
            floor = None
        await state.update_data(floor=floor)
        await message.answer("Введіть номер квартири (якщо є, інакше введіть '-' ):")
        await state.set_state(Form.apartment)
    except Exception as e:
        logging.error(f"Помилка у process_floor: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.apartment))
async def process_apartment(message: types.Message, state: FSMContext):
    logging.debug("Entered process_apartment handler")
    try:
        apartment = message.text.strip()
        if apartment == "-":
            apartment = None
        data = await state.get_data()
        async with async_session() as session:
            address = Address(
                user_id=data["user_id"],
                city=data["city"],
                street=data["street"],
                house=data["house"],
                entrance=data.get("entrance"),
                floor=data.get("floor"),
                apartment=apartment
            )
            session.add(address)
            await session.commit()
            await state.update_data(address_id=address.id)

        await message.answer("Оберіть комунальну послугу:", reply_markup=menu_keyboards())
        await state.set_state(Form.service)
    except Exception as e:
        logging.error(f"Помилка у process_apartment: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")