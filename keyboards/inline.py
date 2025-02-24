# keyboards/inline.py
from typing import Any, Coroutine
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# def start_keyboard() -> InlineKeyboardMarkup:
#     start_button = InlineKeyboardButton(text="Start", callback_data="start_")
#     return InlineKeyboardMarkup(inline_keyboard=[[start_button]])
#
# def merge_keyboards(specific: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
#     default_kb = start_keyboard()
#     merged = InlineKeyboardMarkup(inline_keyboard=specific.inline_keyboard + default_kb.inline_keyboard)
#     return merged

def menu_keyboards(address_id: int = None, user_id: int = None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Електроенергія", callback_data="service_electricity")],
        [InlineKeyboardButton(text="Газ та Газопостачання", callback_data="service_gas")],
        [InlineKeyboardButton(text="Вивіз сміття", callback_data="service_trash")]
    ]
    if address_id is not None:
        buttons.append([InlineKeyboardButton(text="Рахунки", callback_data=f"bill_address_{address_id}")])
    elif user_id is not None:
        buttons.append([InlineKeyboardButton(text="Адреси", callback_data=f"start_{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def electricity_keyboards() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Однозонний", callback_data="elec_one"),
             InlineKeyboardButton(text="Двозонний", callback_data="elec_two")],
            [InlineKeyboardButton(text="Трьохзонний", callback_data="elec_three")]
        ]
    )
    return kb
