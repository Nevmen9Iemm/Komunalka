# utils/helpers.py
import logging
from sqlalchemy import select
from models import User, Address
from db import async_session

async def get_or_create_user(telegram_id: int, user_name: str) -> User:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if not user:
            user = User(telegram_id=telegram_id, user_name=user_name)
            session.add(user)
            await session.commit()
        return user

async def load_addresses(user_id: int):
    async with async_session() as session:
        stmt = select(Address).where(Address.user_id == user_id)
        result = await session.execute(stmt)
        addresses = result.scalars().all()
    return addresses

def build_address_inline_keyboard(addresses) -> tuple[str, any]:
    """
    Формує текст повідомлення та inline клавіатуру для вибору адрес.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    text = "Ваші збережені адреси:\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for addr in addresses:
        addr_text = f"{addr.city}, {addr.street}, {addr.house}"
        if addr.apartment:
            addr_text += f", кв. {addr.apartment}"
        text += addr_text + "\n"
        kb.inline_keyboard.append([InlineKeyboardButton(text=addr_text, callback_data=f"select_address_{addr.id}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Додати нову адресу", callback_data="add_new_address")])
    return text, kb
