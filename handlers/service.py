from keyboards.inline import electricity_keyboards
from handlers.form_states import Form
from loader import dp, bot
from handlers.electricity import *


@dp.callback_query(lambda c: c.data and c.data.startswith("service_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_service handler")
    try:
        service = callback.data.split("_")[1]
        await state.update_data(service=service)
        await callback.answer()
        if service == "electricity":
            logging.debug("Electricity service")
            await callback.message.edit_text(
                "Оберіть тип лічильника для електроенергії або натисніть \"/start\" для вибору адреси:",
                reply_markup=electricity_keyboards()
            )
            await state.set_state(Form.electricity_type)
        elif service == "gas":
            logging.debug("Gas service")
            await callback.message.edit_text(
                "Введіть поточні показники лічильника газу:",
                reply_markup=None
            )
            await state.set_state(Form.gas_current)
        elif service == "trash":
            logging.debug("Trash service")
            await callback.message.edit_text(
                "Введіть кількість відвантажень:",
                reply_markup=None
            )
            await state.set_state(Form.trash_unloads)
        elif service == "bills":
            logging.debug("Bills service")
            await callback.message.edit_text(
                "Ваші рахунки або натисніть \"/start\" для вибору адреси:",
                reply_markup=None
            )
            await state.set_state(Form.bill_address)
    except Exception as e:
        logging.exception("Помилка у process_service:")
        await callback.message.edit_text(
            "Сталася помилка. Спробуйте пізніше. Натисніть кнопку \"/start\" для продовження",
            reply_markup=None
        )


# Обробка вибору типу лічильника для електроенергії
@dp.callback_query(lambda c: c.data in ["elec_one", "elec_two", "elec_three"])
async def process_electricity_type(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_electricity_type handler")
    try:
        elec_type = callback.data
        await state.update_data(electricity_type=elec_type)
        await bot.answer_callback_query(callback.id)
        if elec_type == "elec_one":
            logging.debug("Entered elec_one")
            await bot.send_message(callback.from_user.id, "Введіть поточні показники лічильника (Однозонний):")
            await state.set_state(Form.elec_one_current)
        elif elec_type == "elec_two":
            logging.debug("Entered elec_two")
            await bot.send_message(callback.from_user.id, "Введіть поточні показники лічильника в зоні 'День':")
            await state.set_state(Form.elec_two_current_day)
        elif elec_type == "elec_three":
            logging.debug("Entered elec_three")
            await bot.send_message(callback.from_user.id, "Введіть поточні показники лічильника в зоні 'Пік':")
            await state.set_state(Form.elec_three_current_peak)
    except Exception as e:
        logging.error(f"Помилка у process_electricity_type: {e}")
        await bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Сталася помилка. Спробуйте пізніше. Натисніть кнопку \"/start\" для продовження",
            reply_markup=None
        )