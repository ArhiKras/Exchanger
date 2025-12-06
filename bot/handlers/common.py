"""
Обработчики команд и общих действий
"""
import logging
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core import create_user
from bot.keyboards import get_main_menu


logger = logging.getLogger(__name__)


def register_common_handlers(dp):
    """Регистрация общих обработчиков"""
    
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        await state.clear()
        user = message.from_user
        create_user(user.id, user.username, user.first_name)
        
        await message.answer(
            f"👋 Привет, {user.first_name}!\n\n"
            "Я — твой личный кошелёк для путешествий! 🌍✈️\n\n"
            "Я помогу тебе отслеживать расходы в разных странах, "
            "конвертировать валюты по актуальным курсам и вести учёт твоих путешествий.\n\n"
            "Выбери действие в меню ниже:",
            reply_markup=get_main_menu()
        )
    
    @dp.callback_query(F.data == "main_menu")
    async def show_main_menu(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.message.edit_text(
            "🏠 Главное меню\n\n"
            "Выбери действие:",
            reply_markup=get_main_menu()
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "cancel")
    async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.message.edit_text(
            "❌ Действие отменено.\n\n"
            "Выбери действие в меню:",
            reply_markup=get_main_menu()
        )
        await callback.answer()

