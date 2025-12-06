"""
Обработчики учёта расходов
"""
import logging
from aiogram import types, F
from aiogram.fsm.context import FSMContext

from core import get_active_trip, add_expense, get_trip_by_id
from services import parse_number, format_amount, format_balance, convert_currency_api
from bot.keyboards import get_main_menu, get_yes_no_keyboard, get_back_to_menu_keyboard


logger = logging.getLogger(__name__)


def register_expense_handlers(dp):
    """Регистрация обработчиков расходов"""
    
    @dp.message(F.text)
    async def process_expense_message(message: types.Message):
        """Обработка сообщений с числами как расходов"""
        user_id = message.from_user.id
        trip = get_active_trip(user_id)
        
        if not trip:
            await message.answer(
                "❌ У тебя нет активного путешествия.\n\n"
                "Создай новое путешествие, чтобы начать учитывать расходы!",
                reply_markup=get_main_menu()
            )
            return
        
        amount = parse_number(message.text)
        
        if amount is None:
            await message.answer(
                "💬 Я не понял, что ты имеешь в виду.\n\n"
                "Отправь мне число (сумму расхода) или выбери действие в меню:",
                reply_markup=get_main_menu()
            )
            return
        
        if amount <= 0:
            await message.answer(
                "❌ Сумма должна быть положительной!",
                reply_markup=get_back_to_menu_keyboard()
            )
            return
        
        # Конвертируем сумму
        result = convert_currency_api(amount, trip['to_currency'], trip['from_currency'])
        
        if not result or 'result' not in result:
            # Если API не работает, используем сохранённый курс
            converted_amount = amount / trip['exchange_rate']
        else:
            converted_amount = result['result']
        
        # Формируем данные для callback
        expense_data = f"{trip['trip_id']}:{amount}:{converted_amount}"
        
        await message.answer(
            f"💸 <b>Новый расход</b>\n\n"
            f"{format_amount(amount, trip['to_currency'])} = "
            f"{format_amount(converted_amount, trip['from_currency'])}\n\n"
            f"Учесть как расход?",
            reply_markup=get_yes_no_keyboard(expense_data)
        )
    
    @dp.callback_query(F.data.startswith("expense_yes:"))
    async def confirm_expense(callback: types.CallbackQuery):
        """Подтверждение расхода"""
        # Парсим данные
        parts = callback.data.split(":", 1)[1].split(":")
        trip_id = int(parts[0])
        amount_to = float(parts[1])
        amount_from = float(parts[2])
        
        trip = get_trip_by_id(trip_id)
        
        if not trip:
            await callback.answer("❌ Путешествие не найдено", show_alert=True)
            return
        
        # Проверяем достаточность баланса
        if trip['current_balance_to'] < amount_to:
            await callback.answer(
                "⚠️ Недостаточно средств на балансе!",
                show_alert=True
            )
            return
        
        # Добавляем расход
        add_expense(trip_id, amount_to, amount_from, trip['exchange_rate'])
        
        # Получаем обновлённый баланс
        trip = get_trip_by_id(trip_id)
        
        await callback.message.edit_text(
            f"✅ <b>Расход учтён!</b>\n\n"
            f"💸 Потрачено: {format_amount(amount_to, trip['to_currency'])} = "
            f"{format_amount(amount_from, trip['from_currency'])}\n\n"
            f"{format_balance(trip['current_balance_to'], trip['to_currency'], trip['current_balance_from'], trip['from_currency'])}",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "expense_no")
    async def cancel_expense(callback: types.CallbackQuery):
        """Отмена расхода"""
        await callback.message.edit_text(
            "❌ Расход не учтён.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.answer()

