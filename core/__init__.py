"""
Ядро приложения - конфигурация и база данных
"""

from .config import (
    BOT_TOKEN,
    CURRENCY_API_KEY,
    DATABASE_PATH,
    COUNTRY_CURRENCY_MAP
)

from .database import (
    init_db,
    create_user,
    create_trip,
    get_user_trips,
    get_trip_by_id,
    get_active_trip,
    set_active_trip,
    add_expense,
    get_trip_expenses,
    update_trip_rate,
    delete_trip
)

__all__ = [
    'BOT_TOKEN',
    'CURRENCY_API_KEY',
    'DATABASE_PATH',
    'COUNTRY_CURRENCY_MAP',
    'init_db',
    'create_user',
    'create_trip',
    'get_user_trips',
    'get_trip_by_id',
    'get_active_trip',
    'set_active_trip',
    'add_expense',
    'get_trip_expenses',
    'update_trip_rate',
    'delete_trip',
]

