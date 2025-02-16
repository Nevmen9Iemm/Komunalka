from typing import Any, Coroutine

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app import bot


def get_menu_keyboard(menu_state: str) -> InlineKeyboardMarkup | Coroutine[Any, Any, InlineKeyboardMarkup]:
    if menu_state == "process_select_address":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Start", callback_data="start")]
            ]
        )
    elif menu_state == "process_service":
        menu_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Електроенергія", callback_data="service_electricity"),
                    InlineKeyboardButton(text="Газ та Газопостачання", callback_data="service_gas")
                ],
                [
                    InlineKeyboardButton(text="Вивіз сміття", callback_data="service_trash"),
                    InlineKeyboardButton(text="Рахунки", callback_data="service_bills")
                ],
                [
                    InlineKeyboardButton(text="Адреси", callback_data="service_bills"),
                ]
            ]
        )
        return menu_kb
    elif menu_state == "process_electricity_type":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Однозонний", callback_data="elec_one"),
                    InlineKeyboardButton(text="Двозонний", callback_data="elec_two")
                ],
                [
                    InlineKeyboardButton(text="Трьохзонний", callback_data="elec_three")
                ]
            ]
        )
    elif menu_state == "process_elec_one_previous":
        return menu_keyboards()
    elif menu_state == "process_elec_two_previous_night":
        return menu_keyboards()
    elif menu_state == "process_elec_three_previous_night":
        return menu_keyboards()
    elif menu_state == "process_gas_previous":
        return menu_keyboards()
    elif menu_state == "process_trash_bins":
        return menu_keyboards()
    elif menu_state == "process_bill_address":
        return menu_keyboards()
    elif menu_state == "process_bill_detail":
        return menu_keyboards()
    elif menu_state == "process_bill_confirm":
        return menu_keyboards()
    else:
        return default_keyboard()

async def default_keyboard(user_id: int = None) -> InlineKeyboardMarkup:
    """Повертає базову клавіатуру з кнопками, які відображаються у кожному стані."""
    default_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Start", callback_data="start_")]
        ]
    )
    if user_id is None:
        user_id = await bot.get_me()
        return default_kb

    else:
        return default_kb


def merge_keyboards(specific: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """Об’єднує специфічну клавіатуру із базовою клавіатурою."""
    default_kb = default_keyboard()
    # Об’єднуємо рядки кнопок: спочатку специфічні, потім базові
    merged_keyboard = InlineKeyboardMarkup(
        inline_keyboard=specific.inline_keyboard + default_kb.inline_keyboard
    )
    return merged_keyboard

# def add_address_keyboard() -> InlineKeyboardMarkup:
#     add_address_kb = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="Додати нову адресу", callback_data="add_new_address")]
#         ]
#     )
#     return add_address_kb

def menu_keyboards(address_id: int = None, user_id: int = None) -> InlineKeyboardMarkup:
    """
    Повертає клавіатуру меню. Якщо address_id задано,
    додатково формує кнопку "Рахунки" з callback_data, що містить address_id.
    """
    buttons = [
        [InlineKeyboardButton(text="Електроенергія", callback_data="service_electricity")],
        [InlineKeyboardButton(text="Газ та Газопостачання", callback_data="service_gas")],
        [InlineKeyboardButton(text="Вивіз сміття", callback_data="service_trash")]
        ]
    # Якщо address_id передано, додаємо кнопку "Рахунки" у той же рядок, або окремо, як вам потрібно
    if address_id is not None:
        # Наприклад, додаємо її в окремий рядок:
        # buttons.insert(-1, [InlineKeyboardButton(text="Рахунки", callback_data=f"bill_address_{address_id}")])
        buttons.append([InlineKeyboardButton(text="Рахунки", callback_data=f"bill_address_{address_id}")])
    elif user_id is not None:
        buttons.append([InlineKeyboardButton(text="Адреси", callback_data=f"start_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def electricity_keyboards() -> InlineKeyboardMarkup:
    electricity_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Однозонний", callback_data="elec_one"),
                InlineKeyboardButton(text="Двозонний", callback_data="elec_two")
            ],
            [
                InlineKeyboardButton(text="Трьохзонний", callback_data="elec_three")
            ]
        ]
    )
    return electricity_kb