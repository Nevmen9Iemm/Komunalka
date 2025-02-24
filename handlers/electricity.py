import logging
import datetime
from aiogram import types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from db import async_session
from models import Bill
from handlers.form_states import Form
from loader import dp

@dp.message(F.text, StateFilter(Form.elec_one_current))
async def process_elec_one_current(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_one_current handler")
    try:
        current = float(message.text.strip())
        await state.update_data(elec_one_current=current)
        await message.answer("Введіть попередні показники лічильника:")
        await state.set_state(Form.elec_one_previous)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_one_current:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_one_previous))
async def process_elec_one_previous(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_one_previous handler")
    try:
        previous = float(message.text.strip())
        data = await state.get_data()
        current = data.get("elec_one_current")
        consumption = current - previous
        tariff = 4.32
        total_cost = consumption * tariff

        async with async_session() as session:
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Електроенергія",
                created_at=datetime.datetime.now(),
                current=int(current),
                previous=int(previous),
                consumption=int(consumption),
                tariff=tariff,
                total_cost=total_cost
            )
            session.add(bill)
            await session.commit()

        bill_text = (
            f"{'-'*47}\n"
            f"Дата: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            f"Послуга: Електроенергія (Однозонний)\n"
            f"Показники: {int(current)} - {int(previous)}\n"
            f"Спожито: {int(consumption)} кВт\n"
            f"Тариф: {tariff:.2f} грн/кВт\n"
            f"{'-'*47}\n"
            f"Вартість: {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
        await state.set_state(Form.start)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_one_previous:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

# Двозонний режим (День та Ніч)
@dp.message(F.text, StateFilter(Form.elec_two_current_day))
async def process_elec_two_current_day(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_two_current_day handler")
    try:
        current_day = float(message.text.strip())
        await state.update_data(elec_two_current_day=current_day)
        await message.answer("Введіть поточні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_two_current_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_two_current_day:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_two_current_night))
async def process_elec_two_current_night(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_two_current_night handler")
    try:
        current_night = float(message.text.strip())
        await state.update_data(elec_two_current_night=current_night)
        await message.answer("Введіть попередні показники лічильника в зоні 'День':")
        await state.set_state(Form.elec_two_previous_day)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_two_current_night:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_two_previous_day))
async def process_elec_two_previous_day(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_two_previous_day handler")
    try:
        previous_day = float(message.text.strip())
        await state.update_data(elec_two_previous_day=previous_day)
        await message.answer("Введіть попередні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_two_previous_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_two_previous_day:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_two_previous_night))
async def process_elec_two_previous_night(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_two_previous_night handler")
    try:
        previous_night = float(message.text.strip())
        data = await state.get_data()
        current_day = data.get("elec_two_current_day")
        current_night = data.get("elec_two_current_night")
        previous_day = data.get("elec_two_previous_day")
        consumption_day = current_day - previous_day
        consumption_night = current_night - previous_night
        total_consumption = consumption_day + consumption_night
        tariff_day = 4.32
        tariff_night = 2.16
        cost_day = consumption_day * tariff_day
        cost_night = consumption_night * tariff_night
        total_cost = cost_day + cost_night

        async with async_session() as session:
            from models import Bill
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Електроенергія",
                created_at=datetime.datetime.now(),
                current_day_2=int(current_day),
                current_night_2=int(current_night),
                previous_day_2=int(previous_day),
                previous_night_2=int(previous_night),
                consumption_day_2=int(consumption_day),
                consumption_night_2=int(consumption_night),
                total_consumption_2=int(total_consumption),
                tariff_day_2=tariff_day,
                tariff_night_2=tariff_night,
                cost_day_2=cost_day,
                cost_night_2=cost_night,
                total_cost_2=total_cost
            )
            session.add(bill)
            await session.commit()
        bill_text = (
            f"{'-'*47}\n"
            f"Дата: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            f"Послуга: Електроенергія (Двозонний)\n"
            f"Показники День: {int(current_day)} - {int(previous_day)}\n"
            f"Показники Ніч: {int(current_night)} - {int(previous_night)}\n"
            f"Спожито День: {int(consumption_day)} кВт\n"
            f"Спожито Ніч: {int(consumption_night)} кВт\n"
            f"Тариф День: {tariff_day:.2f} грн/кВт\n"
            f"Тариф Ніч: {tariff_night:.2f} грн/кВт\n"
            f"{'-'*47}\n"
            f"Вартість: {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
        await state.set_state(Form.start)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_two_previous_night:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

# Трьохзонний режим
@dp.message(F.text, StateFilter(Form.elec_three_current_peak))
async def process_elec_three_current_peak(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_three_current_peak handler")
    try:
        current_peak = float(message.text.strip())
        await state.update_data(elec_three_current_peak=current_peak)
        await message.answer("Введіть поточні показники лічильника в зоні 'День':")
        await state.set_state(Form.elec_three_current_day)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_three_current_peak:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_three_current_day))
async def process_elec_three_current_day(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_three_current_day handler")
    try:
        current_day = float(message.text.strip())
        await state.update_data(elec_three_current_day=current_day)
        await message.answer("Введіть поточні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_three_current_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_three_current_day:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_three_current_night))
async def process_elec_three_current_night(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_three_current_night handler")
    try:
        current_night = float(message.text.strip())
        await state.update_data(elec_three_current_night=current_night)
        await message.answer("Введіть попередні показники лічильника в зоні 'Пік':")
        await state.set_state(Form.elec_three_previous_peak)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_three_current_night:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_three_previous_peak))
async def process_elec_three_previous_peak(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_three_previous_peak handler")
    try:
        previous_peak = float(message.text.strip())
        await state.update_data(elec_three_previous_peak=previous_peak)
        await message.answer("Введіть попередні показники лічильника в зоні 'День':")
        await state.set_state(Form.elec_three_previous_day)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_three_previous_peak:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_three_previous_day))
async def process_elec_three_previous_day(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_three_previous_day handler")
    try:
        previous_day = float(message.text.strip())
        await state.update_data(elec_three_previous_day=previous_day)
        await message.answer("Введіть попередні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_three_previous_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_three_previous_day:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")

@dp.message(F.text, StateFilter(Form.elec_three_previous_night))
async def process_elec_three_previous_night(message: types.Message, state: FSMContext):
    logging.debug("Entered process_elec_three_previous_night handler")
    try:
        previous_night = float(message.text.strip())
        data = await state.get_data()
        current_peak = data.get("elec_three_current_peak")
        current_day = data.get("elec_three_current_day")
        current_night = data.get("elec_three_current_night")
        previous_peak = data.get("elec_three_previous_peak")
        previous_day = data.get("elec_three_previous_day")
        consumption_peak = current_peak - previous_peak
        consumption_day = current_day - previous_day
        consumption_night = current_night - previous_night
        total_consumption = consumption_peak + consumption_day + consumption_night
        tariff_peak = 6.48
        tariff_day = 4.32
        tariff_night = 1.728
        cost_peak = consumption_peak * tariff_peak
        cost_day = consumption_day * tariff_day
        cost_night = consumption_night * tariff_night
        total_cost = cost_peak + cost_day + cost_night

        async with async_session() as session:
            from models import Bill
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Електроенергія",
                created_at=datetime.datetime.now(),
                current_peak=int(current_peak),
                current_day_3=int(current_day),
                current_night_3=int(current_night),
                previous_peak=int(previous_peak),
                previous_day_3=int(previous_day),
                previous_night_3=int(previous_night),
                consumption_peak=int(consumption_peak),
                consumption_day_3=int(consumption_day),
                consumption_night_3=int(consumption_night),
                total_consumption_3=int(total_consumption),
                tariff_peak=tariff_peak,
                tariff_day_3=tariff_day,
                tariff_night_3=tariff_night,
                cost_peak=cost_peak,
                cost_day_3=cost_day,
                cost_night_3=cost_night,
                total_cost_3=total_cost
            )
            session.add(bill)
            await session.commit()

        bill_text = (
            f"{'-'*47}\n"
            f"Дата: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
            f"Послуга: Електроенергія (Трьохзонний)\n"
            f"Показники Пік: {int(current_peak)} - {int(previous_peak)}\n"
            f"Показники День: {int(current_day)} - {int(previous_day)}\n"
            f"Показники Ніч: {int(current_night)} - {int(previous_night)}\n"
            f"Спожито Пік: {int(consumption_peak)} кВт\n"
            f"Спожито День: {int(consumption_day)} кВт\n"
            f"Спожито Ніч: {int(consumption_night)} кВт\n"
            f"Тариф Пік: {tariff_peak:.2f} грн/кВт\n"
            f"Тариф День: {tariff_day:.2f} грн/кВт\n"
            f"Тариф Ніч: {tariff_night:.2f} грн/кВт\n"
            f"{'-'*47}\n"
            f"Загальна вартість: {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
        await state.set_state(Form.start)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.exception("Помилка у process_elec_three_previous_night:")
        await message.answer("Сталася помилка. Спробуйте пізніше.")
