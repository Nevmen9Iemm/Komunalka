komunalka/
├── app.py                 # Точка входу, конфігурація та запуск бота
├── config.py              # Конфігураційні параметри (наприклад, TG_TOKEN)
├── models.py              # ORM‑моделі (User, Address, Bill)
├── db.py                  # Налаштування бази даних (engine, async_session, init_db, async_clear_old_bills)
├── handlers/              # Обробники повідомлень та callback
│   ├── __init__.py
│   ├── start.py           # Хендлер для /start та обробка користувача і адрес
│   ├── address.py         # Хендлери, пов’язані з адресами (вибір, додавання)
│   ├── service.py         # Хендлер для вибору послуг
│   └── bills.py           # Хендлери перегляду та деталей рахунків
├── keyboards/             # Клавіатури: inline та reply
│   ├── __init__.py
│   ├── inline.py          # Inline клавіатури (Start, меню послуг, адрес тощо)
│   └── reply.py           # Reply клавіатури (постійна клавіатура, наприклад, "Розпочати")
└── utils/                 # Допоміжні функції та утиліти (наприклад, для роботи з користувачами)
    ├── __init__.py
    └── helpers.py         # Функції get_or_create_user, load_addresses, build_keyboard і т.д.
