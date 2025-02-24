# app.py
import logging
import asyncio


from loader import bot
from db import init_db, async_clear_old_bills
from handlers.address import process_select_address, process_add_new_address
from handlers.bills import process_bill_address, process_bill_detail
from handlers.electricity import *
from handlers.form_states import Form
from handlers.gas import *
from handlers.service import process_service
from handlers.start import cmd_start
from handlers.trash import process_trash_unloads, process_trash_bins


# імпортуємо інші обробники, якщо необхідно
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Функція, що виконується при старті: ініціалізація БД та очищення старих рахунків
async def on_startup():
    await init_db()
    await async_clear_old_bills()
    logging.info("Bot started.")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        # Дозволяє коректно завершити асинхронні генератори
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
