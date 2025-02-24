import logging
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from models import Bill
from db import async_session
from keyboards.inline import menu_keyboards
from handlers.form_states import Form
from loader import dp

@dp.callback_query(F.data.startswith("bill_address_"))
async def process_bill_address(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_bill_address handler")
    try:
        data = await state.get_data()
        logging.debug(f"FSM data: {data}")
        if "address_id" not in data:
            raise ValueError("address_id не знайдено у FSM")
        stmt = select(Bill).where(Bill.address_id == data["address_id"]).order_by(Bill.created_at.desc())
        async with async_session() as session:
            result = await session.execute(stmt)
            bills = result.scalars().all()

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            for bill in bills:
                created_at_str = bill.created_at.strftime("%d-%m-%Y") if bill.created_at else "N/A"
                if bill.service == "Електроенергія":
                    total_cost = bill.total_cost or bill.total_cost_2 or bill.total_cost_3
                elif bill.service == "Газ та Газопостачання":
                    total_cost = bill.total_cost_gas
                elif bill.service == "Вивіз сміття":
                    total_cost = bill.total_cost_trash
                else:
                    total_cost = 0
                total_cost_str = f"{total_cost:.2f}"
                bill_text = f"{bill.id}. {created_at_str}, {bill.service}, {total_cost_str} грн"
                keyboard.inline_keyboard.append(
                    [InlineKeyboardButton(text=bill_text, callback_data=f"bill_detail_{bill.id}")]
                )
            if bills:
                await callback.message.edit_text(
                    "Ваші збережені рахунки комунальних послуг або натисніть \"/start\" для вибору адреси:",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    "Рахунки за вибраною адресою не знайдено. Натисніть \"/start\" для вибору адреси:",
                    reply_markup=None
                )
        await state.clear()
    except Exception as e:
        logging.exception("Помилка у process_bill_address:")
        await callback.message.edit_text(
            "Сталася помилка. Спробуйте пізніше. Натисніть кнопку \"/start\" для продовження",
            reply_markup=None
        )

@dp.callback_query(F.data.startswith("bill_detail_"))
async def process_bill_detail(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_bill_detail handler")
    try:
        bill_id = int(callback.data.split("_")[-1])
        async with async_session() as session:
            stmt = select(Bill).where(Bill.id == bill_id)
            result = await session.execute(stmt)
            bill = result.scalars().first()
        if not bill:
            await callback.message.answer("Рахунок не знайдено.")
            return

        created_at_str = bill.created_at.strftime("%d-%m-%Y %H:%M") if bill.created_at else "N/A"
        details = f"Рахунок №{bill_id}\nДата: {created_at_str}\nПослуга: {bill.service}\n\n"
        if bill.service == "Електроенергія":
            if bill.total_cost is not None:
                details += "Тип: Однозонний\n"
                details += f"Поточні показники: {int(bill.current)}\n"
                details += f"Попередні показники: {int(bill.previous)}\n"
                details += f"Спожито: {int(bill.consumption)}\n"
                details += f"Тариф: {bill.tariff}\n"
                details += f"Загальна вартість: {bill.total_cost:.2f} грн\n"
            elif bill.total_cost_2 is not None:
                details += "Тип: Двозонний\n"
                details += f"Поточні показники (День): {int(bill.current_day_2)}\n"
                details += f"Попередні показники (День): {int(bill.previous_day_2)}\n"
                details += f"Поточні показники (Ніч): {int(bill.current_night_2)}\n"
                details += f"Попередні показники (Ніч): {int(bill.previous_night_2)}\n"
                details += f"Спожито (День): {int(bill.consumption_day_2)}\n"
                details += f"Спожито (Ніч): {int(bill.consumption_night_2)}\n"
                details += f"Тариф (День): {bill.tariff_day_2}\n"
                details += f"Тариф (Ніч): {bill.tariff_night_2}\n"
                details += f"Загальна вартість: {bill.total_cost_2:.2f} грн\n"
            elif bill.total_cost_3 is not None:
                details += "Тип: Трьохзонний\n"
                details += f"Поточні показники (Пік): {int(bill.current_peak)}\n"
                details += f"Попередні показники (Пік): {int(bill.previous_peak)}\n"
                details += f"Поточні показники (День): {int(bill.current_day_3)}\n"
                details += f"Попередні показники (День): {int(bill.previous_day_3)}\n"
                details += f"Поточні показники (Ніч): {int(bill.current_night_3)}\n"
                details += f"Попередні показники (Ніч): {int(bill.previous_night_3)}\n"
                details += f"Загальна вартість: {bill.total_cost_3:.2f} грн\n"
            else:
                details += "Дані по електроенергії відсутні.\n"
        elif bill.service == "Газ та Газопостачання":
            details += f"Поточні показники: {int(bill.gas_current)}\n"
            details += f"Попередні показники: {int(bill.gas_previous)}\n"
            details += f"Спожито газу: {int(bill.gas_consumption)}\n"
            details += f"Тариф газ: {bill.tariff_gas}\n"
            details += f"Тариф газопостачання: {bill.tariff_gas_supply}\n"
            details += f"Вартість газу: {bill.cost_gas:.2f} грн\n"
            details += f"Вартість газопостачання: {bill.cost_gas_supply:.2f} грн\n"
            details += f"Загальна вартість: {bill.total_cost_gas:.2f} грн\n"
        elif bill.service == "Вивіз сміття":
            details += f"Кількість відвантажень: {int(bill.unloads)}\n"
            details += f"Кількість сміттєвих баків: {int(bill.bins)}\n"
            details += f"Тариф: {bill.trash_tariff}\n"
            details += f"Загальна вартість: {bill.total_cost_trash:.2f} грн\n"
        else:
            details += "Додаткових даних немає.\n"

        await callback.message.edit_text(
            f"Ваш детальний рахунок:\n\n{details}\nДля вибору адреси натисніть \"/start\".",
            reply_markup=None
        )
    except Exception as e:
        logging.exception("Помилка у process_bill_detail:")
        await callback.message.edit_text(
            "Сталася помилка. Спробуйте пізніше. Натисніть кнопку \"/start\" для продовження",
            reply_markup=None
        )
