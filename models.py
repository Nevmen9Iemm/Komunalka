# models.py
import datetime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey

Base = declarative_base()

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
    current = Column(Integer, nullable=True)
    previous = Column(Integer, nullable=True)
    consumption = Column(Integer, nullable=True)
    tariff = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    # Двозонна електроенергія
    current_day_2 = Column(Integer, nullable=True)
    current_night_2 = Column(Integer, nullable=True)
    previous_day_2 = Column(Integer, nullable=True)
    previous_night_2 = Column(Integer, nullable=True)
    consumption_day_2 = Column(Integer, nullable=True)
    consumption_night_2 = Column(Integer, nullable=True)
    total_consumption_2 = Column(Integer, nullable=True)
    tariff_day_2 = Column(Float, nullable=True)
    tariff_night_2 = Column(Float, nullable=True)
    cost_day_2 = Column(Float, nullable=True)
    cost_night_2 = Column(Float, nullable=True)
    total_cost_2 = Column(Float, nullable=True)
    # Трьохзонна електроенергія
    current_peak = Column(Integer, nullable=True)
    previous_peak = Column(Integer, nullable=True)
    consumption_peak = Column(Integer, nullable=True)
    current_day_3 = Column(Integer, nullable=True)
    previous_day_3 = Column(Integer, nullable=True)
    consumption_day_3 = Column(Integer, nullable=True)
    current_night_3 = Column(Integer, nullable=True)
    previous_night_3 = Column(Integer, nullable=True)
    consumption_night_3 = Column(Integer, nullable=True)
    total_consumption_3 = Column(Integer, nullable=True)
    tariff_peak = Column(Float, nullable=True)
    tariff_day_3 = Column(Float, nullable=True)
    tariff_night_3 = Column(Float, nullable=True)
    cost_peak = Column(Float, nullable=True)
    cost_day_3 = Column(Float, nullable=True)
    cost_night_3 = Column(Float, nullable=True)
    total_cost_3 = Column(Float, nullable=True)
    # Газ та Газопостачання
    gas_current = Column(Integer, nullable=True)
    gas_previous = Column(Integer, nullable=True)
    gas_consumption = Column(Integer, nullable=True)
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
