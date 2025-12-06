import requests
from typing import Optional, Dict, Any
from core.config import CURRENCY_API_KEY


def get_currency_for_country(country: str, country_map: Dict[str, str]) -> Optional[str]:
    """Получить валюту для страны"""
    return country_map.get(country)


def convert_currency_api(amount: float, from_currency: str, to_currency: str) -> Optional[Dict[str, Any]]:
    """
    Конвертировать валюту через API
    Возвращает словарь с результатом или None при ошибке
    """
    try:
        url = "http://api.exchangerate.host/convert"
        params = {
            "access_key": CURRENCY_API_KEY,
            "from": from_currency,
            "to": to_currency,
            "amount": amount
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # Логируем ответ для отладки
        print(f"API Response: {data}")
        
        if data.get("success"):
            return data
        else:
            # Логируем ошибку API
            error_info = data.get("error", {})
            print(f"API Error: {error_info}")
            return None
            
    except Exception as e:
        print(f"Error in convert_currency_api: {e}")
        return None


def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[float]:
    """
    Получить текущий курс обмена между двумя валютами
    """
    result = convert_currency_api(1, from_currency, to_currency)
    if result:
        # Проверяем разные варианты структуры ответа
        if "info" in result:
            # Вариант 1: info.rate
            if "rate" in result["info"]:
                return result["info"]["rate"]
            # Вариант 2: info.quote
            if "quote" in result["info"]:
                return result["info"]["quote"]
        # Вариант 3: result напрямую
        if "result" in result:
            return result["result"]
    return None


def format_amount(amount: float, currency: str) -> str:
    """
    Форматировать сумму для отображения
    """
    return f"{amount:,.2f} {currency}".replace(",", " ")


def format_balance(balance_to: float, to_currency: str, 
                  balance_from: float, from_currency: str) -> str:
    """
    Форматировать баланс в обеих валютах
    """
    to_str = format_amount(balance_to, to_currency)
    from_str = format_amount(balance_from, from_currency)
    return f"💰 Остаток: {to_str} = {from_str}"


def parse_number(text: str) -> Optional[float]:
    """
    Попытаться распарсить число из текста
    """
    try:
        # Убираем пробелы и запятые
        text = text.replace(" ", "").replace(",", ".")
        return float(text)
    except:
        return None


def format_trip_info(trip: Dict[str, Any]) -> str:
    """
    Форматировать информацию о путешествии
    """
    info = f"🌍 {trip['from_country']} → {trip['to_country']}\n\n"
    info += f"💱 Курс: 1 {trip['from_currency']} = {trip['exchange_rate']:.4f} {trip['to_currency']}\n\n"
    info += f"💼 Начальная сумма:\n"
    info += f"   {format_amount(trip['initial_amount_from'], trip['from_currency'])}\n"
    info += f"   {format_amount(trip['initial_amount_to'], trip['to_currency'])}\n\n"
    info += format_balance(
        trip['current_balance_to'], trip['to_currency'],
        trip['current_balance_from'], trip['from_currency']
    )
    return info


def format_expense_history(expenses: list, trip: Dict[str, Any]) -> str:
    """
    Форматировать историю расходов
    """
    if not expenses:
        return "📊 История расходов\n\nРасходов пока нет."
    
    text = f"📊 История расходов\n"
    text += f"🌍 {trip['from_country']} → {trip['to_country']}\n\n"
    
    total_to = 0
    total_from = 0
    
    for expense in expenses[:20]:  # Показываем последние 20 расходов
        total_to += expense['amount_to']
        total_from += expense['amount_from']
        
        date = expense['created_at'].split()[0] if ' ' in expense['created_at'] else expense['created_at']
        text += f"📅 {date}\n"
        text += f"   {format_amount(expense['amount_to'], trip['to_currency'])} = "
        text += f"{format_amount(expense['amount_from'], trip['from_currency'])}\n"
        
        if expense.get('description'):
            text += f"   💬 {expense['description']}\n"
        text += "\n"
    
    if len(expenses) > 20:
        text += f"... и ещё {len(expenses) - 20} расходов\n\n"
    
    text += f"Всего потрачено:\n"
    text += f"{format_amount(total_to, trip['to_currency'])} = "
    text += f"{format_amount(total_from, trip['from_currency'])}"
    
    return text


def validate_currency_pair(from_currency: str, to_currency: str) -> bool:
    """
    Проверить, доступна ли валютная пара через API
    """
    rate = get_exchange_rate(from_currency, to_currency)
    return rate is not None

