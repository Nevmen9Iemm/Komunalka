import logging
import datetime
import asyncio

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.client.bot import DefaultBotProperties

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, select

import config  # Файл config.py повинен містити змінну TG_TOKEN
from keyboards.inline import electricity_keyboards

# Налаштування логування
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Асинхронне налаштування бази даних
DATABASE_URL = "sqlite+aiosqlite:///komunalka_v1.0.1.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# Моделі БД
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    user_name = Column(String, nullable=False)
    addresses = relationship("Address", backref="user")
    bills = relationship("Bill", backref="user")

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    city = Column(String)
    street = Column(String)
    house = Column(String)
    entrance = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    apartment = Column(String, nullable=True)
    bills = relationship("Bill", backref="address")

class Bill(Base):
    __tablename__ = 'bills'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    address_id = Column(Integer, ForeignKey('addresses.id'))
    service = Column(String)  # "Електроенергія", "Газ та Газопостачання", "Вивіз сміття"
    created_at = Column(DateTime, default=datetime.datetime.now)
    # Однозонна електроенергія
    current = Column(Float, nullable=True)
    previous = Column(Float, nullable=True)
    consumption = Column(Float, nullable=True)
    tariff = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    # Двозонна електроенергія (поля із суфіксом _2)
    current_day_2 = Column(Float, nullable=True)
    current_night_2 = Column(Float, nullable=True)
    previous_day_2 = Column(Float, nullable=True)
    previous_night_2 = Column(Float, nullable=True)
    consumption_day_2 = Column(Float, nullable=True)
    consumption_night_2 = Column(Float, nullable=True)
    total_consumption_2 = Column(Float, nullable=True)
    tariff_day_2 = Column(Float, nullable=True)
    tariff_night_2 = Column(Float, nullable=True)
    cost_day_2 = Column(Float, nullable=True)
    cost_night_2 = Column(Float, nullable=True)
    total_cost_2 = Column(Float, nullable=True)
    # Трьохзонна електроенергія (поля із суфіксом _3)
    current_peak = Column(Float, nullable=True)
    previous_peak = Column(Float, nullable=True)
    consumption_peak = Column(Float, nullable=True)
    current_day_3 = Column(Float, nullable=True)
    previous_day_3 = Column(Float, nullable=True)
    consumption_day_3 = Column(Float, nullable=True)
    current_night_3 = Column(Float, nullable=True)
    previous_night_3 = Column(Float, nullable=True)
    consumption_night_3 = Column(Float, nullable=True)
    total_consumption_3 = Column(Float, nullable=True)
    tariff_peak = Column(Float, nullable=True)
    tariff_day_3 = Column(Float, nullable=True)
    tariff_night_3 = Column(Float, nullable=True)
    cost_peak = Column(Float, nullable=True)
    cost_day_3 = Column(Float, nullable=True)
    cost_night_3 = Column(Float, nullable=True)
    total_cost_3 = Column(Float, nullable=True)
    # Газ та Газопостачання
    gas_current = Column(Float, nullable=True)
    gas_previous = Column(Float, nullable=True)
    gas_consumption = Column(Float, nullable=True)
    tariff_gas = Column(Float, nullable=True)
    tariff_gas_supply = Column(Float, nullable=True)
    cost_gas = Column(Float, nullable=True)
    cost_gas_supply = Column(Float, nullable=True)
    total_cost_gas = Column(Float, nullable=True)
    # Вивіз сміття
    unloads = Column(Integer, nullable=True)
    bins = Column(Integer, nullable=True)
    trash_tariff = Column(Float, nullable=True)
    total_cost_trash = Column(Float, nullable=True)

# Ініціалізація БД
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Database initialized.")

# Очищення старих рахунків (старіше 2 років)
async def async_clear_old_bills():
    try:
        async with async_session() as session:
            two_years_ago = datetime.datetime.now() - datetime.timedelta(days=2*365)
            stmt = select(Bill).where(Bill.created_at < two_years_ago)
            result = await session.execute(stmt)
            old_bills = result.scalars().all()
            for bill in old_bills:
                await session.delete(bill)
            await session.commit()
            logging.info("Старі рахунки очищено.")
    except Exception as e:
        logging.error(f"Помилка при очищенні старих рахунків: {e}")


# FSM – визначення станів
class Form(StatesGroup):
    start = State()
    telegram_id = State()
    city = State()
    street = State()
    house = State()
    entrance = State()
    floor = State()
    apartment = State()
    # вибір існуючої адреси або додавання нової
    address_confirm = State()
    # Визначення стану
    service = State()
    electricity_type = State()
    # Однозонний
    elec_one_current = State()
    elec_one_previous = State()
    # Двозонний
    elec_two_current_day = State()
    elec_two_current_night = State()
    elec_two_previous_day = State()
    elec_two_previous_night = State()
    # Трьохзонний
    elec_three_current_peak = State()
    elec_three_current_day = State()
    elec_three_current_night = State()
    elec_three_previous_peak = State()
    elec_three_previous_day = State()
    elec_three_previous_night = State()
    # Газ та Газопостачання
    gas_current = State()
    gas_previous = State()
    # Вивіз сміття
    trash_unloads = State()
    trash_bins = State()
    # Рахунки
    bill_address = State()
    # Вибір адреси
    select_address = State()


# Ініціалізація бота та диспетчера
bot = Bot(token=config.TG_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    logging.debug("Entered start handler")
    # Отримуємо telegram id та ім'я користувача
    telegram_id = message.from_user.id
    user_name = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
    try:
        async with async_session() as session:
            # Шукаємо користувача за telegram_id
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if not user:
                logging.debug("User not found, creating new record")
                user = User(telegram_id=telegram_id, user_name=user_name)
                session.add(user)
                # Оновлюємо дані FSM
                await state.update_data(user_id=user.id, telegram_id=telegram_id, user_name=user_name)
                # Повідомляємо користувача та переходимо до наступного стану
                await message.answer("Ваші дані записано.\nВведіть адресу.\nВведіть місто:")
                await state.set_state(Form.city)
            else:
                logging.debug("User found")
                await state.update_data(user_id=user.id, telegram_id=telegram_id, user_name=user_name)
                stmt = select(Address).where(Address.user_id == user.id)
                result = await session.execute(stmt)
                addresses = result.scalars().all()
                if addresses:
                    logging.debug("Address found")
                    text = "Ваші збережені адреси:\n"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                    for addr in addresses:
                        addr_text = f"{addr.city}, {addr.street}, {addr.house}"
                        if addr.apartment:
                            addr_text += f", кв. {addr.apartment}"
                        # Додаємо перелік адрес у заговолок
                        # text += addr_text + "\n"
                        # Додаємо кожну кнопку як окремий рядок (список кнопок)
                        keyboard.inline_keyboard.append(
                            [InlineKeyboardButton(text=addr_text, callback_data=f"select_address_{addr.id}")]
                        )
                    keyboard.inline_keyboard.append(
                        [InlineKeyboardButton(text="Додати нову адресу", callback_data="add_new_address")]
                    )
                    await message.answer(text, reply_markup=keyboard)
                    await state.set_state(Form.address_confirm)
                else:
                    logging.debug("Address not found")
                    await message.answer("Адреси не знайдено. Введіть адресу.\nВведіть місто:")
                    await state.set_state(Form.city)

    except Exception as e:
        logging.error(f"Error in cmd_start: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


# -------------------- Message Handlers --------------------
# Для кожного message handler використовуємо фільтр F для перевірки стану
# Обробка введення адреси
@dp.message(F.text, StateFilter(Form.city))
async def process_city(message: types.Message, state: FSMContext):
    logging.debug("Entered process_city handler")
    try:
        await state.update_data(city=message.text.strip())
        await message.answer("Введіть вулицю:")
        await state.set_state(Form.street)
    except Exception as e:
        logging.error(f"Помилка у process_city: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.street))
async def process_street(message: types.Message, state: FSMContext):
    logging.debug("Entered process_street handler")
    try:
        await state.update_data(street=message.text.strip())
        await message.answer("Введіть номер будинку:")
        await state.set_state(Form.house)
    except Exception as e:
        logging.error(f"Помилка у process_street: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.house))
async def process_house(message: types.Message, state: FSMContext):
    logging.debug("Entered process_house handler")
    try:
        await state.update_data(house=message.text.strip())
        await message.answer("Введіть під'їзд (якщо є, інакше введіть '-' ):")
        await state.set_state(Form.entrance)
    except Exception as e:
        logging.error(f"Помилка у process_house: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.entrance))
async def process_entrance(message: types.Message, state: FSMContext):
    logging.debug("Entered process_entrance handler")
    try:
        entrance = message.text.strip()
        if entrance == "-":
            entrance = None
        await state.update_data(entrance=entrance)
        await message.answer("Введіть поверх (якщо є, інакше введіть '-' ):")
        await state.set_state(Form.floor)
    except Exception as e:
        logging.error(f"Помилка у process_entrance: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.floor))
async def process_floor(message: types.Message, state: FSMContext):
    logging.debug("Entered process_floor handler")
    try:
        floor = message.text.strip()
        if floor == "-":
            floor = None
        await state.update_data(floor=floor)
        await message.answer("Введіть номер квартири (якщо є, інакше введіть '-' ):")
        await state.set_state(Form.apartment)
    except Exception as e:
        logging.error(f"Помилка у process_floor: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.apartment))
async def process_apartment(message: types.Message, state: FSMContext):
    logging.debug("Entered process_apartment handler")
    try:
        apartment = message.text.strip()
        if apartment == "-":
            apartment = None
        data = await state.get_data()
        async with async_session() as session:
            address = Address(
                user_id=data["user_id"],
                city=data["city"],
                street=data["street"],
                house=data["house"],
                entrance=data.get("entrance"),
                floor=data.get("floor"),
                apartment=apartment
            )
            session.add(address)
            await session.commit()
            await state.update_data(address_id=address.id)
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
            [InlineKeyboardButton(text="Електроенергія", callback_data="service_electricity")],
            [InlineKeyboardButton(text="Газ та Газопостачання", callback_data="service_gas")],
            [InlineKeyboardButton(text="Вивіз сміття", callback_data="service_trash")],
            [InlineKeyboardButton(text="Рахунки", callback_data="service_bills]")]
            ]
        )
        await message.answer("Оберіть комунальну послугу:", reply_markup=keyboard)
        await state.set_state(Form.service)
    except Exception as e:
        logging.error(f"Помилка у process_apartment: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


# @dp.message()
# async def default_handler(message: types.Message, state: FSMContext):
#     current_state = await state.get_state()
#     logging.debug(f"Default handler: message.text = {message.text}, current_state = {current_state}")

# -------------------- Callback Query Handlers --------------------

# Callback для вибору існуючої адреси чи додавання нової
@dp.callback_query(F.data.startswith("select_address_"))
async def process_select_address(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_select_address handler")
    try:
        current_state = await state.get_state()
        if current_state != Form.address_confirm.state:
            return
        # Отримуємо id адреси із callback data
        addr_id = int(callback.data.split("_")[-1])
        await state.update_data(address_id=addr_id)
        await bot.answer_callback_query(callback.id)

        # Завантажуємо дані адреси з бази даних
        async with async_session() as session:
            stmt = select(Address).where(Address.id == addr_id)
            result = await session.execute(stmt)
            address = result.scalars().first()
            if address:
                full_address = f"{address.city}, {address.street}, {address.house}"
                if address.apartment:
                    full_address += f", кв. {address.apartment}"
            else:
                full_address = "невідома адреса"

        data = await state.get_data()
        address_id = data.get("address_id")

        # Формуємо клавіатуру для вибору комунальних послуг
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="Електроенергія", callback_data="service_electricity")]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="Газ та Газопостачання", callback_data="service_gas")]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="Вивіз сміття", callback_data="service_trash")]
        )
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="Рахунки", callback_data=f"bill_address_{address_id}")]
        )

        # Відправляємо повідомлення з отриманою адресою
        await bot.send_message(
            callback.from_user.id,
            f"Оберіть комунальну послугу для адреси {full_address}:",
            reply_markup=keyboard
        )
        await state.set_state(Form.service)
    except Exception as e:
        logging.error(f"Помилка у process_select_address: {e}")
        await bot.send_message(callback.from_user.id, "Сталася помилка. Спробуйте пізніше.")


@dp.callback_query(lambda c: c.data == "add_new_address")
async def process_add_new_address(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_add_new_address handler")
    try:
        await bot.answer_callback_query(callback.id)
        await bot.send_message(callback.from_user.id, "Введіть місто:")
        await state.set_state(Form.city)
    except Exception as e:
        logging.error(f"Помилка у process_add_new_address: {e}")
        await bot.send_message(callback.from_user.id, "Сталася помилка. Спробуйте пізніше.")


# Обробка вибору послуги
@dp.callback_query(lambda c: c.data and c.data.startswith("service_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
    logging.debug("Entered process_service handler")
    try:
        service = callback.data.split("_")[1]
        await state.update_data(service=service)
        await bot.answer_callback_query(callback.id)
        if service == "electricity":
            keyboard = electricity_keyboards()
            await bot.send_message(callback.from_user.id, "Оберіть тип лічильника для електроенергії:", reply_markup=keyboard)
            await state.set_state(Form.electricity_type)
        elif service == "gas":
            await bot.send_message(callback.from_user.id, "Введіть поточні показники лічильника газу:")
            await state.set_state(Form.gas_current)
        elif service == "trash":
            await bot.send_message(callback.from_user.id, "Введіть кількість відвантажень:")
            await state.set_state(Form.trash_unloads)
        elif service == "bills":
            await state.set_state(Form.bill_address)

    except Exception as e:
        logging.error(f"Помилка у process_service: {e}")
        await bot.send_message(callback.from_user.id, "Сталася помилка. Спробуйте пізніше.")


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
        await bot.send_message(callback.from_user.id, "Сталася помилка. Спробуйте пізніше.")


# ----------------- Перегляд рахунків -----------------
@dp.callback_query(F.data.startswith("bill_address_"))
async def process_bill_address(callback: types.CallbackQuery, state: FSMContext):
    try:
        logging.debug("Entered process_bill_address handler")
        data = await state.get_data()
        logging.debug(f"FSM data: {data}")

        # Переконайтеся, що address_id присутній
        if "address_id" not in data:
            raise ValueError("address_id не знайдено у FSM")

        # Сортуємо рахунки за датою (останні рахунки будуть на початку)
        stmt = select(Bill).where(Bill.address_id == data["address_id"]).order_by(Bill.created_at.desc())
        async with async_session() as session:
            result = await session.execute(stmt)
            bills = result.scalars().all()

            # Створюємо клавіатуру із пустим списком рядків
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            # Нумеруємо рахунки, починаючи з 1
            for idx, bill in enumerate(bills, start=1):
                created_at_str = bill.created_at.strftime("%Y-%m-%d %H:%M:%S") if bill.created_at else "N/A"

                # Визначаємо загальну вартість залежно від типу послуги
                if bill.service == "Електроенергія":
                    total_cost = bill.total_cost or bill.total_cost_2 or bill.total_cost_3
                elif bill.service == "Газ та Газопостачання":
                    total_cost = bill.total_cost_gas
                elif bill.service == "Вивіз сміття":
                    total_cost = bill.total_cost_trash
                else:
                    total_cost = 0

                # Округлюємо вартість до 2-х десяткових
                total_cost_str = f"{total_cost:.2f}"
                bill_text = f"{idx}. {created_at_str}, {bill.service}, {total_cost_str} грн"
                keyboard.inline_keyboard.append(
                    [InlineKeyboardButton(text=bill_text, callback_data=f"bill_detail_{bill.id}")]
                )

            if bills:
                await bot.send_message(
                    callback.from_user.id,
                    "Ваші збережені рахунки комунальних послуг:",
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(callback.from_user.id, "Рахунки за вибраною адресою не знайдено.")
        await state.clear()
    except Exception as e:
        logging.error(f"Помилка у process_bill_address: {e}")
        await bot.send_message(callback.from_user.id, "Сталася помилка. Спробуйте пізніше.")


@dp.callback_query(F.data.startswith("bill_detail_"))
async def process_bill_detail(callback: types.CallbackQuery, state: FSMContext):
    try:
        logging.debug("Entered process_bill_detail handler")
        # Отримуємо id рахунку з callback data
        bill_id = int(callback.data.split("_")[-1])

        async with async_session() as session:
            stmt = select(Bill).where(Bill.id == bill_id)
            result = await session.execute(stmt)
            bill = result.scalars().first()

        if not bill:
            await bot.send_message(callback.from_user.id, "Рахунок не знайдено.")
            return

        # Форматуємо дату
        created_at_str = bill.created_at.strftime("%Y-%m-%d %H:%M:%S") if bill.created_at else "N/A"
        details = f"Рахунок №{bill_id}\nДата: {created_at_str}\nПослуга: {bill.service}\n\n"

        if bill.service == "Електроенергія":
            if bill.total_cost is not None:
                details += "Тип: Однозонний\n"
                details += f"Поточні показники: {bill.current}\n"
                details += f"Попередні показники: {bill.previous}\n"
                details += f"Спожито: {bill.consumption}\n"
                details += f"Тариф: {bill.tariff}\n"
                details += f"Загальна вартість: {bill.total_cost:.2f} грн\n"
            elif bill.total_cost_2 is not None:
                details += "Тип: Двозонний\n"
                details += f"Поточні показники (День): {bill.current_day_2}\n"
                details += f"Попередні показники (День): {bill.previous_day_2}\n"
                details += f"Поточні показники (Ніч): {bill.current_night_2}\n"
                details += f"Попередні показники (Ніч): {bill.previous_night_2}\n"
                details += f"Спожито (День): {bill.consumption_day_2}\n"
                details += f"Спожито (Ніч): {bill.consumption_night_2}\n"
                details += f"Тариф (День): {bill.tariff_day_2}\n"
                details += f"Тариф (Ніч): {bill.tariff_night_2}\n"
                details += f"Загальна вартість: {bill.total_cost_2:.2f} грн\n"
            elif bill.total_cost_3 is not None:
                details += "Тип: Трьохзонний\n"
                details += f"Поточні показники (Пік): {bill.current_peak}\n"
                details += f"Попередні показники (Пік): {bill.previous_peak}\n"
                details += f"Поточні показники (День): {bill.current_day_3}\n"
                details += f"Попередні показники (День): {bill.previous_day_3}\n"
                details += f"Поточні показники (Ніч): {bill.current_night_3}\n"
                details += f"Попередні показники (Ніч): {bill.previous_night_3}\n"
                details += f"Спожито (Пік): {bill.consumption_peak}\n"
                details += f"Спожито (День): {bill.consumption_day_3}\n"
                details += f"Спожито (Ніч): {bill.consumption_night_3}\n"
                details += f"Тариф (Пік): {bill.tariff_peak}\n"
                details += f"Тариф (День): {bill.tariff_day_3}\n"
                details += f"Тариф (Ніч): {bill.tariff_night_3}\n"
                details += f"Загальна вартість: {bill.total_cost_3:.2f} грн\n"
            else:
                details += "Дані по електроенергії відсутні.\n"
        elif bill.service == "Газ та Газопостачання":
            details += f"Поточні показники: {bill.gas_current}\n"
            details += f"Попередні показники: {bill.gas_previous}\n"
            details += f"Спожито газу: {bill.gas_consumption}\n"
            details += f"Тариф газ: {bill.tariff_gas}\n"
            details += f"Тариф газопостачання: {bill.tariff_gas_supply}\n"
            details += f"Загальна вартість: {bill.total_cost_gas:.2f} грн\n"
        elif bill.service == "Вивіз сміття":
            details += f"Кількість відвантажень: {bill.unloads}\n"
            details += f"Кількість сміттєвих баків: {bill.bins}\n"
            details += f"Тариф: {bill.trash_tariff}\n"
            details += f"Загальна вартість: {bill.total_cost_trash:.2f} грн\n"
        else:
            details += "Додаткових даних немає.\n"

        await bot.send_message(callback.from_user.id, details)
        await bot.answer_callback_query(callback.id)
    except Exception as e:
        logging.error(f"Помилка у process_bill_detail: {e}")
        await bot.send_message(callback.from_user.id, "Сталася помилка при завантаженні деталей рахунку.")


# -------------------- Решта Message Handlers --------------------

# ----------------- Електроенергія: Однозонний -----------------
@dp.message(F.text, StateFilter(Form.elec_one_current))
async def process_elec_one_current(message: types.Message, state: FSMContext):
    try:
        current = float(message.text.strip())
        await state.update_data(elec_one_current=current)
        await message.answer("Введіть попередні показники лічильника:")
        await state.set_state(Form.elec_one_previous)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_one_current: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_one_previous))
async def process_elec_one_previous(message: types.Message, state: FSMContext):
    try:
        previous = float(message.text.strip())
        data = await state.get_data()
        current = data.get("elec_one_current")
        consumption = current - previous
        tariff = 4.32
        total_cost = consumption * tariff

        # Завантаження даних адреси з БД за id
        async with async_session() as session:

            # Додавання рахунку в БД
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Електроенергія",
                created_at=datetime.datetime.now(),
                current=current,
                previous=previous,
                consumption=consumption,
                tariff=tariff,
                total_cost=total_cost
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

        # Дістаємо user_name із бази даних та зберігаємо у змінну user_name
        async with async_session():
            user_name = data["user_name"]

        # Формування рахунку з округленням числових значень до 2-х десяткових
        bill_text = (
            f"{'-' * 47}\n"
            f"Дата:    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Користувач:    {user_name}\n"
            f"Адреса:    {city}, {street}, {house}, {apartment}\n"
            f"{'-' * 47}\n"
            f"Послуга:    Електроенергія (Однозонний)\n"
            f"Показники:    {int(current)} - {int(previous)}\n"
            f"Спожито:    {int(consumption)} кВт\n"
            f"Тариф:    {tariff:.2f} грн/кВт\n"
            f"{'-' * 47}\n"
            f"Вартість:    {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_two_previous_night: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


# ----------------- Електроенергія: Двозонний -----------------
@dp.message(F.text, StateFilter(Form.elec_two_current_day))
async def process_elec_two_current_day(message: types.Message, state: FSMContext):
    try:
        current_day = float(message.text.strip())
        await state.update_data(elec_two_current_day=current_day)
        await message.answer("Введіть поточні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_two_current_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_two_current_day: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_two_current_night))
async def process_elec_two_current_night(message: types.Message, state: FSMContext):
    try:
        current_night = float(message.text.strip())
        await state.update_data(elec_two_current_night=current_night)
        await message.answer("Введіть попередні показники лічильника в зоні 'День':")
        await state.set_state(Form.elec_two_previous_day)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_two_current_night: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_two_previous_day))
async def process_elec_two_previous_day(message: types.Message, state: FSMContext):
    try:
        previous_day = float(message.text.strip())
        await state.update_data(elec_two_previous_day=previous_day)
        await message.answer("Введіть попередні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_two_previous_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_two_previous_day: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_two_previous_night))
async def process_elec_two_previous_night(message: types.Message, state: FSMContext):
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

        # Завантаження даних адреси з БД за id
        async with async_session() as session:
            # Додавання рахунку в БД
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Електроенергія",
                created_at=datetime.datetime.now(),
                current_day_2=current_day,
                current_night_2=current_night,
                previous_day_2=previous_day,
                previous_night_2=previous_night,
                consumption_day_2=consumption_day,
                consumption_night_2=consumption_night,
                total_consumption_2=total_consumption,
                tariff_day_2=tariff_day,
                tariff_night_2=tariff_night,
                cost_day_2=cost_day,
                cost_night_2=cost_night,
                total_cost_2=total_cost
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

        async with async_session():
            user_name = data["user_name"]

        # Формування рахунку з округленням числових значень до 2-х десяткових
        bill_text = (
            f"{'-' * 47}\n"
            f"Дата:    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Користувач:    {user_name}\n"
            f"Адреса:    {city}, {street}, {house}, {apartment}\n"
            f"{'-' * 47}\n"
            f"Послуга:    Електроенергія (Двозонний)\n"
            f"Показники День:    {int(current_day)} - {int(previous_day)}\n"
            f"Показники Ніч:    {int(current_night)} - {int(previous_night)}\n"
            f"Спожито День:    {int(consumption_day)} кВт\n"
            f"Спожито Ніч:    {int(consumption_night)} кВт\n"
            f"Тариф День:    {tariff_day:.2f} грн/кВт\n"
            f"Тариф Ніч:    {tariff_night:.2f} грн/кВт\n"
            f"{'-' * 47}\n"
            f"Загальна вартість:    {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_two_previous_night: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


# ----------------- Електроенергія: Трьохзонний -----------------
@dp.message(F.text, StateFilter(Form.elec_three_current_peak))
async def process_elec_three_current_peak(message: types.Message, state: FSMContext):
    try:
        current_peak = float(message.text.strip())
        await state.update_data(elec_three_current_peak=current_peak)
        await message.answer("Введіть поточні показники лічильника в зоні 'День':")
        await state.set_state(Form.elec_three_current_day)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_three_current_peak: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_three_current_day))
async def process_elec_three_current_day(message: types.Message, state: FSMContext):
    try:
        current_day = float(message.text.strip())
        await state.update_data(elec_three_current_day=current_day)
        await message.answer("Введіть поточні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_three_current_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_three_current_day: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_three_current_night))
async def process_elec_three_current_night(message: types.Message, state: FSMContext):
    try:
        current_night = float(message.text.strip())
        await state.update_data(elec_three_current_night=current_night)
        await message.answer("Введіть попередні показники лічильника в зоні 'Пік':")
        await state.set_state(Form.elec_three_previous_peak)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_three_current_night: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_three_previous_peak))
async def process_elec_three_previous_peak(message: types.Message, state: FSMContext):
    try:
        previous_peak = float(message.text.strip())
        await state.update_data(elec_three_previous_peak=previous_peak)
        await message.answer("Введіть попередні показники лічильника в зоні 'День':")
        await state.set_state(Form.elec_three_previous_day)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_three_previous_peak: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_three_previous_day))
async def process_elec_three_previous_day(message: types.Message, state: FSMContext):
    try:
        previous_day = float(message.text.strip())
        await state.update_data(elec_three_previous_day=previous_day)
        await message.answer("Введіть попередні показники лічильника в зоні 'Ніч':")
        await state.set_state(Form.elec_three_previous_night)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_three_previous_day: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.elec_three_previous_night))
async def process_elec_three_previous_night(message: types.Message, state: FSMContext):
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

        # Завантаження даних адреси з БД за id
        async with async_session() as session:
            # Додавання рахунку в БД
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Електроенергія",
                created_at=datetime.datetime.now(),
                current_peak=current_peak,
                current_day_3=current_day,
                current_night_3=current_night,
                previous_peak=previous_peak,
                previous_day_3=previous_day,
                previous_night_3=previous_night,
                consumption_peak=consumption_peak,
                consumption_day_3=consumption_day,
                consumption_night_3=consumption_night,
                total_consumption_3=total_consumption,
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

        async with async_session():
            user_name = data["user_name"]

        # Формування рахунку з округленням числових значень до 2-х десяткових
        bill_text = (
            f"{'-' * 47}\n"
            f"Дата:    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Користувач:    {user_name}\n"
            f"Адреса:    {city}, {street}, {house}, {apartment}\n"
            f"{'-' * 47}\n"
            f"Послуга:    лектроенергія (Трьохзонний)\n"
            f"Показники Пік:    {int(current_peak)} - {int(previous_peak)}\n"
            f"Показники День:    {int(current_day)} - {int(previous_day)}\n"
            f"Показники Ніч:    {int(current_night)} - {int(previous_night)}\n"
            f"Спожито Пік:    {int(consumption_peak)} кВт\n"
            f"Спожито День:    {int(consumption_day)} кВт\n"
            f"Спожито Ніч:    {int(consumption_night)} кВт\n"
            f"Тариф Пік:    {tariff_peak:.2f} грн/кВт\n"
            f"Тариф День:    {tariff_day:.2f} грн/кВт\n"
            f"Тариф Ніч:    {tariff_night:.2f} грн/кВт\n"
            f"{'-' * 47}\n"
            f"Загальна вартість:    {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_elec_three_previous_night: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


# ----------------- Газ та Газопостачання -----------------
@dp.message(F.text, StateFilter(Form.gas_current))
async def process_gas_current(message: types.Message, state: FSMContext):
    try:
        current = float(message.text.strip())
        await state.update_data(gas_current=current)
        await message.answer("Введіть попередні показники лічильника газу:")
        await state.set_state(Form.gas_previous)
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_gas_current: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.gas_previous))
async def process_gas_previous(message: types.Message, state: FSMContext):
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

        # Завантаження даних адреси з БД за id
        async with async_session() as session:

            # Запис рахунку в БД
            bill = Bill(
                user_id=data["user_id"],
                address_id=data["address_id"],
                service="Газ та Газопостачання",
                created_at=datetime.datetime.now(),
                gas_current=current,
                gas_previous=previous,
                gas_consumption=gas_consumption,
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
            city = addr_obj.city
            street = addr_obj.street or ""
            house = addr_obj.house or ""
            apartment = addr_obj.apartment or ""
        else:
            city, street, house, apartment = "", "", "", ""

        async with async_session():
            user_name = data["user_name"]

        # Формування рахунку з округленням числових значень до 2-х десяткових
        bill_text = (
            f"{'-' * 47}\n"
            f"Дата:    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"користувач:    {user_name}\n"
            f"Адреса:    {city}, {street}, {house}, {apartment}\n"
            f"{'-' * 47}\n"
            f"Послуга:    Газ та Газопостачання\n"
            f"Показники:    {int(current)} - {int(previous)}\n"
            f"Спожито:    {int(gas_consumption)} м³\n"
            f"Тариф Газ:    {tariff_gas:.2f} грн/м³\n"
            f"Тариф Газопостачання:    {tariff_supply:.2f} грн/м³\n"
            f"Вартість Газ:    {cost_gas:.2f} грн\n"
            f"Вартість Газопостачання:    {cost_supply:.2f} грн\n"
            f"{'-' * 47}\n"
            f"Загальна вартість:    {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_gas_previous: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


# ----------------- Вивіз сміття -----------------
@dp.message(F.text, StateFilter(Form.trash_unloads))
async def process_trash_unloads(message: types.Message, state: FSMContext):
    try:
        if not message.text.isdigit():
            await message.answer("Введіть числове значення.")
            return
        await state.update_data(trash_unloads=int(message.text.strip()))
        await message.answer("Введіть кількість сміттєвих баків:")
        await state.set_state(Form.trash_bins)
    except Exception as e:
        logging.error(f"Помилка у process_trash_unloads: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


@dp.message(F.text, StateFilter(Form.trash_bins))
async def process_trash_bins(message: types.Message, state: FSMContext):
    try:
        if not message.text.isdigit():
            await message.answer("Введіть числове значення.")
            return
        bins = int(message.text.strip())
        data = await state.get_data()
        unloads = data.get("trash_unloads")
        tariff = 165
        total_cost = unloads * bins * tariff

        # Завантаження даних адреси з БД за id
        async with async_session() as session:

            # Запис рахунку в БД
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

        async with async_session():
            user_name = data["user_name"]

        # Формування рахунку з округленням числових значень до 2-х десяткових
        bill_text = (
            f"{'-' * 47}\n"
            f"Дата:    {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Користувач:    {user_name}\n"
            f"Адреса: {city}, {street}, {house}, {apartment}\n"
            f"{'-' * 47}\n"
            f"Послуга:    Вивіз сміття\n"
            f"Відвантаження:    {int(unloads)}\n"
            f"Сміттєві баки:    {int(bins)}\n"
            f"Тариф: {tariff:.2f} грн\n"
            f"{'-' * 47}\n"
            f"Загальна вартість:    {total_cost:.2f} грн"
        )
        await message.answer(bill_text)
        await state.clear()
    except ValueError:
        await message.answer("Введіть числове значення.")
    except Exception as e:
        logging.error(f"Помилка у process_trash_bins: {e}")
        await message.answer("Сталася помилка. Спробуйте пізніше.")


# Функція, що виконується при старті: ініціалізація БД та очищення старих рахунків
async def on_startup():
    await init_db()
    await async_clear_old_bills()
    logging.info("Bot started.")

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())


if __name__ == '__main__':
    asyncio.run(main())

