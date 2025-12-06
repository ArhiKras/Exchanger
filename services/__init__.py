"""
Сервисы - API клиент и утилиты
"""

from .api_client import (
    get_current_rate,
    convert_currency,
    get_all_supported_currencies
)

from .utils import (
    get_currency_for_country,
    convert_currency_api,
    get_exchange_rate,
    format_amount,
    format_balance,
    parse_number,
    format_trip_info,
    format_expense_history,
    validate_currency_pair
)

__all__ = [
    'get_current_rate',
    'convert_currency',
    'get_all_supported_currencies',
    'get_currency_for_country',
    'convert_currency_api',
    'get_exchange_rate',
    'format_amount',
    'format_balance',
    'parse_number',
    'format_trip_info',
    'format_expense_history',
    'validate_currency_pair',
]

