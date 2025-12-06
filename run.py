"""
Точка входа приложения
Запуск Telegram-бота Traveler Wallet
"""
import asyncio
from bot.main import start_bot


if __name__ == "__main__":
    print("=" * 60)
    print("🌍 Traveler Wallet Bot")
    print("=" * 60)
    print("Запуск бота...")
    print()
    
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")

