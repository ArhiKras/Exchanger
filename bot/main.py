"""
Главный файл бота - точка входа
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core import BOT_TOKEN, init_db
from bot.handlers import register_all_handlers


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start_bot():
    """Запуск бота"""
    # Инициализация базы данных
    init_db()
    logger.info("База данных инициализирована")
    
    # Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация обработчиков
    register_all_handlers(dp)
    logger.info("Обработчики зарегистрированы")
    
    logger.info("Бот запущен!")
    
    # Запуск бота
    await dp.start_polling(bot)


async def main():
    """Главная функция"""
    await start_bot()


if __name__ == "__main__":
    asyncio.run(main())

