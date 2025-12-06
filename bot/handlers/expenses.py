"""
Обработчики учёта расходов
"""
import logging
from aiogram import types, F
from aiogram.fsm.context import FSMContext

from core import get_active_trip, add_expense, get_trip_by_id
from services import parse_number, format_amount, format_balance, convert_currency_api
from bot.keyboards import get_main_menu, get_yes_no_keyboard, get_back_to_menu_keyboard, get_cancel_keyboard
from bot.states import ExpenseComment


logger = logging.getLogger(__name__)


def register_expense_handlers(dp):
    """Регистрация обработчиков расходов"""
    
    # ВАЖНО: Обработчик комментария должен быть первым (до общего обработчика текста)
    @dp.message(ExpenseComment.waiting_comment)
    async def process_comment(message: types.Message, state: FSMContext):
        """Обработка комментария к расходу"""
        comment = message.text.strip()
        data = await state.get_data()
        expense_data = data.get('expense_data', '')
        
        # Парсим данные
        parts = expense_data.split(":")
        trip_id = int(parts[0])
        amount_to = float(parts[1])
        amount_from = float(parts[2])
        
        trip = get_trip_by_id(trip_id)
        
        if not trip:
            await message.answer("❌ Путешествие не найдено", reply_markup=get_main_menu())
            await state.clear()
            return
        
        # Проверяем достаточность баланса
        if trip['current_balance_to'] < amount_to:
            await message.answer(
                "⚠️ Недостаточно средств на балансе!",
                reply_markup=get_back_to_menu_keyboard()
            )
            await state.clear()
            return
        
        # Добавляем расход с комментарием
        add_expense(trip_id, amount_to, amount_from, trip['exchange_rate'], comment)
        
        # Получаем обновлённый баланс
        trip = get_trip_by_id(trip_id)
        
        await message.answer(
            f"✅ Расход учтён!\n\n"
            f"💸 Потрачено: {format_amount(amount_to, trip['to_currency'])} = "
            f"{format_amount(amount_from, trip['from_currency'])}\n"
            f"💬 Комментарий: {comment}\n\n"
            f"{format_balance(trip['current_balance_to'], trip['to_currency'], trip['current_balance_from'], trip['from_currency'])}",
            reply_markup=get_back_to_menu_keyboard()
        )
        await state.clear()
    
    @dp.message(F.text)
    async def process_expense_message(message: types.Message, state: FSMContext):
        """Обработка сообщений с числами как расходов"""
        # Проверяем, не находимся ли мы в каком-то состоянии
        current_state = await state.get_state()
        if current_state is not None:
            # Если в состоянии, пропускаем - его обработает другой handler
            return
        
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
            f"💸 Новый расход\n\n"
            f"{format_amount(amount, trip['to_currency'])} = "
            f"{format_amount(converted_amount, trip['from_currency'])}\n\n"
            f"Хочешь добавить комментарий или сразу учесть расход?",
            reply_markup=get_yes_no_keyboard(expense_data)
        )
    
    @dp.callback_query(F.data.startswith("expense_yes:"))
    async def confirm_expense(callback: types.CallbackQuery):
        """Подтверждение расхода без комментария"""
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
        
        # Добавляем расход без комментария
        add_expense(trip_id, amount_to, amount_from, trip['exchange_rate'])
        
        # Получаем обновлённый баланс
        trip = get_trip_by_id(trip_id)
        
        await callback.message.edit_text(
            f"✅ Расход учтён!\n\n"
            f"💸 Потрачено: {format_amount(amount_to, trip['to_currency'])} = "
            f"{format_amount(amount_from, trip['from_currency'])}\n\n"
            f"{format_balance(trip['current_balance_to'], trip['to_currency'], trip['current_balance_from'], trip['from_currency'])}",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("expense_comment:"))
    async def ask_comment(callback: types.CallbackQuery, state: FSMContext):
        """Запрос комментария к расходу"""
        # Сохраняем данные о расходе в состояние
        expense_data = callback.data.split(":", 1)[1]
        await state.update_data(expense_data=expense_data)
        
        await callback.message.edit_text(
            "💬 Введи комментарий к расходу:\n"
            "Например: Обед в ресторане, Такси, Сувениры и т.д.",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        await state.set_state(ExpenseComment.waiting_comment)
    
    @dp.callback_query(F.data == "expense_no")
    async def cancel_expense(callback: types.CallbackQuery):
        """Отмена расхода"""
        await callback.message.edit_text(
            "❌ Расход не учтён.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await callback.answer()
