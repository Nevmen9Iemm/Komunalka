import logging
import datetime
from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from models import Bill, Address
from db import async_session
from aiogram.types import ReplyKeyboardRemove
from handlers.form_states import Form
from loader import dp

@dp.message(F.text, StateFilter(Form.trash_unloads))
async def process_trash_unloads(message: types.Message, state: FSMContext):
    logging.debug("Entered process_trash_unloads handler")
    try:
        if not message.text.isdigit():
            await message.answer("Введіть числове значення.")
            return
        await state.update_data(trash_unloads=int(message.text.strip()))
        await message.answer("Введіть кількість сміттєвих баків:")
        await state.set_state(Form.trash_bins)
    except Exception as e:
        logging.exception("Помилка у process_trash_unloads:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.trash_bins))
async def process_trash_bins(message: types.Message, state: FSMContext):
    logging.debug("Entered process_trash_bins handler")
    try:
        if not message.text.isdigit():
            await message.answer("Введіть числове значення.")
            return
        bins = int(message.text.strip())
        data = await state.get_data()
        unloads = data.get("trash_unloads")
        tariff = 160
        total_cost = unloads * bins * tariff

        async with async_session() as session:
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Вивіз сміття",
                created_at=datetime.datetime.now(),
                unloads=unloads,
                bins=bins,
                trash_tariff=tariff,
                total_cost_trash=total_cost
            )
            session.add(bill)
            await session.commit()

            stmt_addr = select(Address).where(Address.id == data["address_id"])
            result_addr = await session.execute(stmt_addr)
            addr_obj = result_addr.scalars().first()

        if addr_obj:
            city = addr_obj.city or ""
            street = addr_obj.street or ""
            house = addr_obj.house or ""
            apartment = addr_obj.apartment or ""
        else:
            city, street, house, apartment = "", "", "", ""

        bill_text = (
            f"{'-'*47}\n"
            f"Дата: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            f"Послуга: Вивіз сміття\n"
            f"Відвантаження: {int(unloads)}\n"
            f"Сміттєві баки: {int(bins)}\n"
            f"Тариф: {tariff:.2f} грн\n"
            f"{'-'*47}\n"
            f"Загальна вартість: {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
        await state.set_state(Form.start)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_trash_bins:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")
