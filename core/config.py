import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Currency API Key
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

# Database
DATABASE_PATH = "traveler_wallet.db"

# Currency to Country mapping
COUNTRY_CURRENCY_MAP = {
    "Россия": "RUB",
    "США": "USD",
    "Китай": "CNY",
    "Япония": "JPY",
    "Великобритания": "GBP",
    "Европа": "EUR",
    "Германия": "EUR",
    "Франция": "EUR",
    "Италия": "EUR",
    "Испания": "EUR",
    "Швейцария": "CHF",
    "Турция": "TRY",
    "ОАЭ": "AED",
    "Таиланд": "THB",
    "Вьетнам": "VND",
    "Индия": "INR",
    "Корея": "KRW",
    "Южная Корея": "KRW",
    "Канада": "CAD",
    "Австралия": "AUD",
    "Новая Зеландия": "NZD",
    "Сингапур": "SGD",
    "Малайзия": "MYR",
    "Индонезия": "IDR",
    "Филиппины": "PHP",
    "Мексика": "MXN",
    "Бразилия": "BRL",
    "Аргентина": "ARS",
    "Польша": "PLN",
    "Чехия": "CZK",
    "Венгрия": "HUF",
    "Норвегия": "NOK",
    "Швеция": "SEK",
    "Дания": "DKK",
    "Израиль": "ILS",
    "Египет": "EGP",
    "ЮАР": "ZAR",
}

