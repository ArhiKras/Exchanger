import requests
from dotenv import load_dotenv
import os

load_dotenv()


# Получение текущих курсов валют
def get_current_rate(default: str = "USD", currencies: list[str] = ["EUR", "GBP", "JPY"]):
    url = "https://api.exchangerate.host/live"
    params = {
        "access_key": os.getenv("CURRENCY_API_KEY"),
        "source": default,
        "currencies": ",".join(currencies)
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data


# Конвертация валюты
def convert_currency(amount: float, from_currency: str, to_currency: str):
    url = "https://api.exchangerate.host/convert"
    params = {
        "access_key": os.getenv("CURRENCY_API_KEY"),
        "from": from_currency,
        "to": to_currency,
        "amount": amount
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data


# Получение всех поддерживаемых валют
def get_all_supported_currencies():
    url = "https://api.exchangerate.host/list"
    params = {
        "access_key": os.getenv("CURRENCY_API_KEY"),
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data


# Точка входа       
if __name__ == "__main__":
    print(convert_currency(100, "RUB", "EUR"))

