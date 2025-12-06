"""
Пакет обработчиков бота
"""

from .common import register_common_handlers
from .trips import register_trip_handlers
from .expenses import register_expense_handlers


def register_all_handlers(dp):
    """Регистрация всех обработчиков"""
    register_common_handlers(dp)
    register_trip_handlers(dp)
    register_expense_handlers(dp)


__all__ = ['register_all_handlers']

