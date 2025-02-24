# keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def persistent_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Повертає постійну Reply клавіатуру з кнопкою "Розпочати".
    """
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/start")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return kb

def main_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Повертає Reply клавіатуру з кнопками для вибору послуг.
    """
    btn_electricity = KeyboardButton(text="Електроенергія 💡")
    btn_gas = KeyboardButton(text="Газ та Газопостачання")
    btn_trash = KeyboardButton(text="Вивіз сміття 🚮")
    btn_bills = KeyboardButton(text="Рахунки 🧾")
    kb = ReplyKeyboardMarkup(
        keyboard=[[btn_electricity, btn_gas], [btn_trash, btn_bills]],
        resize_keyboard=True
    )
    return kb
