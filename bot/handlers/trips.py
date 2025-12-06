"""
Обработчики создания и управления путешествиями
"""
import logging
from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core import (
    COUNTRY_CURRENCY_MAP,
    create_trip,
    get_user_trips,
    get_active_trip,
    set_active_trip,
    get_trip_by_id,
    get_trip_expenses,
    update_trip_rate,
    delete_trip
)
from services import (
    get_currency_for_country,
    get_exchange_rate,
    format_amount,
    format_balance,
    parse_number,
    format_trip_info,
    format_expense_history,
    convert_currency_api
)
from bot.keyboards import (
    get_main_menu,
    get_cancel_keyboard,
    get_rate_confirmation_keyboard,
    get_trips_keyboard,
    get_trip_actions_keyboard,
    get_confirm_delete_keyboard
)
from bot.states import TripCreation, RateChange


logger = logging.getLogger(__name__)


def register_trip_handlers(dp):
    """Регистрация обработчиков путешествий"""
    
    # === СОЗДАНИЕ ПУТЕШЕСТВИЯ ===
    
    @dp.callback_query(F.data == "new_trip")
    @dp.message(Command("newtrip"))
    async def start_trip_creation(event: types.Message | types.CallbackQuery, state: FSMContext):
        """Начало создания путешествия"""
        await state.clear()
        
        countries_list = "\n".join([f"• {country}" for country in sorted(COUNTRY_CURRENCY_MAP.keys())])
        text = (
            "🌍 <b>Создание нового путешествия</b>\n\n"
            "Введи страну отправления (откуда едешь):\n\n"
            f"{countries_list}\n\n"
            "Или введи название своей страны."
        )
        
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_cancel_keyboard())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_cancel_keyboard())
        
        await state.set_state(TripCreation.waiting_from_country)
    
    @dp.message(TripCreation.waiting_from_country)
    async def process_from_country(message: types.Message, state: FSMContext):
        """Обработка страны отправления"""
        from_country = message.text.strip()
        from_currency = get_currency_for_country(from_country, COUNTRY_CURRENCY_MAP)
        
        if not from_currency:
            await message.answer(
                f"❌ Не удалось определить валюту для страны '{from_country}'.\n\n"
                "Попробуй выбрать из списка или напиши название точнее.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await state.update_data(from_country=from_country, from_currency=from_currency)
        
        countries_list = "\n".join([f"• {country}" for country in sorted(COUNTRY_CURRENCY_MAP.keys())])
        await message.answer(
            f"✅ Отлично! Валюта отправления: {from_currency}\n\n"
            "Теперь введи страну назначения (куда едешь):\n\n"
            f"{countries_list}",
            reply_markup=get_cancel_keyboard()
        )
        
        await state.set_state(TripCreation.waiting_to_country)
    
    @dp.message(TripCreation.waiting_to_country)
    async def process_to_country(message: types.Message, state: FSMContext):
        """Обработка страны назначения"""
        to_country = message.text.strip()
        to_currency = get_currency_for_country(to_country, COUNTRY_CURRENCY_MAP)
        
        if not to_currency:
            await message.answer(
                f"❌ Не удалось определить валюту для страны '{to_country}'.\n\n"
                "Попробуй выбрать из списка или напиши название точнее.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        data = await state.get_data()
        from_currency = data['from_currency']
        
        if from_currency == to_currency:
            await message.answer(
                "❌ Валюты совпадают! Выбери другую страну назначения.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Проверяем валютную пару через API
        await message.answer("⏳ Проверяю курс обмена...")
        
        rate = get_exchange_rate(from_currency, to_currency)
        
        if rate is None:
            await message.answer(
                "❌ Не удалось получить курс обмена от API.\n"
                "Попробуй позже или введи курс вручную.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await state.update_data(
            to_country=to_country, 
            to_currency=to_currency, 
            api_rate=rate
        )
        
        await message.answer(
            f"💱 <b>Текущий курс обмена:</b>\n\n"
            f"1 {from_currency} = {rate:.4f} {to_currency}\n\n"
            f"Этот курс тебе подходит?",
            reply_markup=get_rate_confirmation_keyboard()
        )
        
        await state.set_state(TripCreation.waiting_rate_decision)
    
    @dp.callback_query(F.data == "rate_accept", TripCreation.waiting_rate_decision)
    async def accept_rate(callback: types.CallbackQuery, state: FSMContext):
        """Принятие курса от API"""
        data = await state.get_data()
        await state.update_data(exchange_rate=data['api_rate'])
        
        await callback.message.edit_text(
            f"✅ Курс принят: 1 {data['from_currency']} = {data['api_rate']:.4f} {data['to_currency']}\n\n"
            f"Теперь введи начальную сумму в {data['from_currency']}, "
            f"которую планируешь взять в путешествие:",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        
        await state.set_state(TripCreation.waiting_initial_amount)
    
    @dp.callback_query(F.data == "rate_manual", TripCreation.waiting_rate_decision)
    async def manual_rate(callback: types.CallbackQuery, state: FSMContext):
        """Запрос ручного ввода курса"""
        data = await state.get_data()
        
        await callback.message.edit_text(
            f"✏️ Введи свой курс обмена.\n\n"
            f"Например, если 1 {data['from_currency']} = 15.5 {data['to_currency']}, "
            f"просто напиши: 15.5",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        
        await state.set_state(TripCreation.waiting_manual_rate)
    
    @dp.message(TripCreation.waiting_manual_rate)
    async def process_manual_rate(message: types.Message, state: FSMContext):
        """Обработка ручного курса"""
        rate = parse_number(message.text)
        
        if rate is None or rate <= 0:
            await message.answer(
                "❌ Неверный формат курса. Введи положительное число, например: 15.5",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        data = await state.get_data()
        await state.update_data(exchange_rate=rate)
        
        await message.answer(
            f"✅ Курс установлен: 1 {data['from_currency']} = {rate:.4f} {data['to_currency']}\n\n"
            f"Теперь введи начальную сумму в {data['from_currency']}, "
            f"которую планируешь взять в путешествие:",
            reply_markup=get_cancel_keyboard()
        )
        
        await state.set_state(TripCreation.waiting_initial_amount)
    
    @dp.message(TripCreation.waiting_initial_amount)
    async def process_initial_amount(message: types.Message, state: FSMContext):
        """Обработка начальной суммы"""
        amount = parse_number(message.text)
        
        if amount is None or amount <= 0:
            await message.answer(
                "❌ Неверная сумма. Введи положительное число, например: 50000",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        data = await state.get_data()
        
        # Конвертируем начальную сумму
        result = convert_currency_api(amount, data['from_currency'], data['to_currency'])
        
        if not result or 'result' not in result:
            await message.answer(
                "❌ Ошибка при конвертации суммы. Попробуй снова.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        initial_amount_to = result['result']
        
        # Создаём путешествие
        trip_id = create_trip(
            user_id=message.from_user.id,
            from_country=data['from_country'],
            to_country=data['to_country'],
            from_currency=data['from_currency'],
            to_currency=data['to_currency'],
            exchange_rate=data['exchange_rate'],
            initial_amount_from=amount,
            initial_amount_to=initial_amount_to
        )
        
        await message.answer(
            f"🎉 <b>Путешествие создано!</b>\n\n"
            f"🌍 {data['from_country']} → {data['to_country']}\n"
            f"💱 Курс: 1 {data['from_currency']} = {data['exchange_rate']:.4f} {data['to_currency']}\n\n"
            f"💼 Твой стартовый баланс:\n"
            f"   {format_amount(amount, data['from_currency'])}\n"
            f"   {format_amount(initial_amount_to, data['to_currency'])}\n\n"
            f"Теперь просто отправляй мне суммы расходов числом, "
            f"и я буду их учитывать! 📊",
            reply_markup=get_main_menu()
        )
        
        await state.clear()
    
    # === МОИ ПУТЕШЕСТВИЯ ===
    
    @dp.callback_query(F.data == "my_trips")
    @dp.message(Command("switch"))
    async def show_trips(event: types.Message | types.CallbackQuery):
        """Показать список путешествий"""
        user_id = event.from_user.id
        trips = get_user_trips(user_id)
        
        if not trips:
            text = "❌ У тебя пока нет путешествий.\n\nСоздай первое!"
            keyboard = get_main_menu()
        else:
            active_trip = get_active_trip(user_id)
            active_trip_id = active_trip['trip_id'] if active_trip else None
            
            text = "✈️ <b>Твои путешествия</b>\n\nВыбери путешествие для просмотра:"
            keyboard = get_trips_keyboard(trips, active_trip_id)
        
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, reply_markup=keyboard)
            await event.answer()
        else:
            await event.answer(text, reply_markup=keyboard)
    
    @dp.callback_query(F.data.startswith("trip_select:"))
    async def show_trip_details(callback: types.CallbackQuery):
        """Показать детали путешествия"""
        trip_id = int(callback.data.split(":")[1])
        trip = get_trip_by_id(trip_id)
        
        if not trip:
            await callback.answer("❌ Путешествие не найдено", show_alert=True)
            return
        
        text = format_trip_info(trip)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_trip_actions_keyboard(trip_id)
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("trip_activate:"))
    async def activate_trip(callback: types.CallbackQuery):
        """Активировать путешествие"""
        trip_id = int(callback.data.split(":")[1])
        set_active_trip(callback.from_user.id, trip_id)
        
        await callback.answer("✅ Путешествие активировано!", show_alert=True)
        await show_trip_details(callback)
    
    @dp.callback_query(F.data.startswith("trip_balance:"))
    async def show_trip_balance(callback: types.CallbackQuery):
        """Показать баланс путешествия"""
        trip_id = int(callback.data.split(":")[1])
        trip = get_trip_by_id(trip_id)
        
        if not trip:
            await callback.answer("❌ Путешествие не найдено", show_alert=True)
            return
        
        text = (
            f"💰 <b>Баланс путешествия</b>\n\n"
            f"🌍 {trip['from_country']} → {trip['to_country']}\n\n"
            f"{format_balance(trip['current_balance_to'], trip['to_currency'], trip['current_balance_from'], trip['from_currency'])}"
        )
        
        await callback.answer(text, show_alert=True)
    
    @dp.callback_query(F.data.startswith("trip_history:"))
    async def show_trip_history(callback: types.CallbackQuery):
        """Показать историю расходов путешествия"""
        trip_id = int(callback.data.split(":")[1])
        trip = get_trip_by_id(trip_id)
        
        if not trip:
            await callback.answer("❌ Путешествие не найдено", show_alert=True)
            return
        
        expenses = get_trip_expenses(trip_id)
        text = format_expense_history(expenses, trip)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_trip_actions_keyboard(trip_id)
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("trip_rate:"))
    async def change_trip_rate(callback: types.CallbackQuery, state: FSMContext):
        """Начать изменение курса"""
        trip_id = int(callback.data.split(":")[1])
        trip = get_trip_by_id(trip_id)
        
        if not trip:
            await callback.answer("❌ Путешествие не найдено", show_alert=True)
            return
        
        await state.update_data(trip_id=trip_id)
        
        await callback.message.edit_text(
            f"💱 <b>Изменение курса</b>\n\n"
            f"🌍 {trip['from_country']} → {trip['to_country']}\n"
            f"Текущий курс: 1 {trip['from_currency']} = {trip['exchange_rate']:.4f} {trip['to_currency']}\n\n"
            f"Введи новый курс обмена:",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        
        await state.set_state(RateChange.waiting_new_rate)
    
    @dp.callback_query(F.data.startswith("trip_delete:"))
    async def confirm_delete_trip(callback: types.CallbackQuery):
        """Подтверждение удаления путешествия"""
        trip_id = int(callback.data.split(":")[1])
        trip = get_trip_by_id(trip_id)
        
        if not trip:
            await callback.answer("❌ Путешествие не найдено", show_alert=True)
            return
        
        await callback.message.edit_text(
            f"⚠️ <b>Удаление путешествия</b>\n\n"
            f"🌍 {trip['from_country']} → {trip['to_country']}\n\n"
            f"Ты уверен? Все данные будут удалены безвозвратно!",
            reply_markup=get_confirm_delete_keyboard(trip_id)
        )
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("trip_delete_confirm:"))
    async def delete_trip_confirmed(callback: types.CallbackQuery):
        """Удаление путешествия"""
        trip_id = int(callback.data.split(":")[1])
        
        delete_trip(trip_id)
        
        await callback.answer("✅ Путешествие удалено", show_alert=True)
        await show_trips(callback)
    
    # === БАЛАНС И ИСТОРИЯ ===
    
    @dp.callback_query(F.data == "balance")
    @dp.message(Command("balance"))
    async def show_balance(event: types.Message | types.CallbackQuery):
        """Показать баланс активного путешествия"""
        user_id = event.from_user.id
        trip = get_active_trip(user_id)
        
        if not trip:
            text = "❌ У тебя нет активного путешествия.\n\nСоздай новое или выбери существующее!"
            keyboard = get_main_menu()
        else:
            text = (
                f"💰 <b>Текущий баланс</b>\n\n"
                f"🌍 {trip['from_country']} → {trip['to_country']}\n\n"
                f"{format_balance(trip['current_balance_to'], trip['to_currency'], trip['current_balance_from'], trip['from_currency'])}\n\n"
                f"💱 Курс: 1 {trip['from_currency']} = {trip['exchange_rate']:.4f} {trip['to_currency']}"
            )
            from bot.keyboards import get_back_to_menu_keyboard
            keyboard = get_back_to_menu_keyboard()
        
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, reply_markup=keyboard)
            await event.answer()
        else:
            await event.answer(text, reply_markup=keyboard)
    
    @dp.callback_query(F.data == "history")
    @dp.message(Command("history"))
    async def show_history(event: types.Message | types.CallbackQuery):
        """Показать историю расходов активного путешествия"""
        user_id = event.from_user.id
        trip = get_active_trip(user_id)
        
        if not trip:
            text = "❌ У тебя нет активного путешествия.\n\nСоздай новое или выбери существующее!"
            keyboard = get_main_menu()
        else:
            expenses = get_trip_expenses(trip['trip_id'])
            text = format_expense_history(expenses, trip)
            from bot.keyboards import get_back_to_menu_keyboard
            keyboard = get_back_to_menu_keyboard()
        
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, reply_markup=keyboard)
            await event.answer()
        else:
            await event.answer(text, reply_markup=keyboard)
    
    # === ИЗМЕНЕНИЕ КУРСА ===
    
    @dp.callback_query(F.data == "change_rate")
    @dp.message(Command("setrate"))
    async def start_rate_change(event: types.Message | types.CallbackQuery, state: FSMContext):
        """Начать изменение курса активного путешествия"""
        user_id = event.from_user.id
        trip = get_active_trip(user_id)
        
        if not trip:
            text = "❌ У тебя нет активного путешествия.\n\nСоздай новое или выбери существующее!"
            keyboard = get_main_menu()
            
            if isinstance(event, types.CallbackQuery):
                await event.message.edit_text(text, reply_markup=keyboard)
                await event.answer()
            else:
                await event.answer(text, reply_markup=keyboard)
            return
        
        await state.update_data(trip_id=trip['trip_id'])
        
        text = (
            f"💱 <b>Изменение курса</b>\n\n"
            f"🌍 {trip['from_country']} → {trip['to_country']}\n"
            f"Текущий курс: 1 {trip['from_currency']} = {trip['exchange_rate']:.4f} {trip['to_currency']}\n\n"
            f"Введи новый курс обмена:"
        )
        
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_cancel_keyboard())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_cancel_keyboard())
        
        await state.set_state(RateChange.waiting_new_rate)
    
    @dp.message(RateChange.waiting_new_rate)
    async def process_new_rate(message: types.Message, state: FSMContext):
        """Обработка нового курса"""
        rate = parse_number(message.text)
        
        if rate is None or rate <= 0:
            await message.answer(
                "❌ Неверный формат курса. Введи положительное число, например: 15.5",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        data = await state.get_data()
        trip_id = data['trip_id']
        
        update_trip_rate(trip_id, rate)
        trip = get_trip_by_id(trip_id)
        
        await message.answer(
            f"✅ <b>Курс обновлён!</b>\n\n"
            f"🌍 {trip['from_country']} → {trip['to_country']}\n"
            f"Новый курс: 1 {trip['from_currency']} = {rate:.4f} {trip['to_currency']}",
            reply_markup=get_main_menu()
        )
        
        await state.clear()

