import logging
import datetime
from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from models import Bill, Address
from db import async_session
from handlers.form_states import Form
from loader import dp

@dp.message(F.text, StateFilter(Form.gas_current))
async def process_gas_current(message: types.Message, state: FSMContext):
    logging.debug("Entered process_gas_current handler")
    try:
        current = float(message.text.strip())
        await state.update_data(gas_current=current)
        await message.answer("Введіть попередні показники лічильника газу:")
        await state.set_state(Form.gas_previous)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_gas_current:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.gas_previous))
async def process_gas_previous(message: types.Message, state: FSMContext):
    logging.debug("Entered process_gas_previous handler")
    try:
        previous = float(message.text.strip())
        data = await state.get_data()
        current = data.get("gas_current")
        gas_consumption = current - previous
        tariff_gas = 7.96
        tariff_supply = 1.308
        cost_gas = gas_consumption * tariff_gas
        cost_supply = gas_consumption * tariff_supply
        total_cost = cost_gas + cost_supply

        async with async_session() as session:
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Газ та Газопостачання",
                created_at=datetime.datetime.now(),
                gas_current=int(current),
                gas_previous=int(previous),
                gas_consumption=int(gas_consumption),
                tariff_gas=tariff_gas,
                tariff_gas_supply=tariff_supply,
                cost_gas=cost_gas,
                cost_gas_supply=cost_supply,
                total_cost_gas=total_cost
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
            f"Послуга: Газ та Газопостачання\n"
            f"Показники: {int(current)} - {int(previous)}\n"
            f"Спожито: {int(gas_consumption)} м³\n"
            f"Тариф Газ: {tariff_gas:.2f} грн/м³\n"
            f"Тариф Газопостачання: {tariff_supply:.3f} грн/м³\n"
            f"Вартість Газ: {cost_gas:.2f} грн\n"
            f"Вартість Газопостачання: {cost_supply:.2f} грн\n"
            f"{'-'*47}\n"
            f"Загальна вартість: {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
        await state.set_state(Form.start)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_gas_previous:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")
