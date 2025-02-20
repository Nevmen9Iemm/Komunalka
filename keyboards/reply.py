from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    service_electricity = KeyboardButton(text="Електроенергія 💡")
    service_gas = KeyboardButton(text="Газ та Газопостачання")
    service_trash = KeyboardButton(text="Вивіз сміття 🚮")
    service_bills = KeyboardButton(text="Рахунки 🧾")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [service_electricity, service_gas],
            [service_trash, service_bills]
        ],
        resize_keyboard=True
    )
    return keyboard


# def persistent_reply_keyboard() -> ReplyKeyboardMarkup:
#     """
#     Повертає постійну Reply клавіатуру з однією кнопкою "Start".
#     Параметр one_time_keyboard=False робить її постійною.
#     """
#     kb = ReplyKeyboardMarkup(
#         keyboard=[[KeyboardButton(text="Start")]],
#         resize_keyboard=True,
#         one_time_keyboard=False  # клавіатура залишатиметься на екрані
#     )
#     return kb


def persistent_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Повертає постійну Reply клавіатуру з кнопкою "Розпочати",
    яка завжди відображається.
    """
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/start")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return kb