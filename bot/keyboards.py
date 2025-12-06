from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Создать новое путешествие", callback_data="new_trip")],
        [InlineKeyboardButton(text="✈️ Мои путешествия", callback_data="my_trips")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="📊 История расходов", callback_data="history")],
        [InlineKeyboardButton(text="💱 Изменить курс", callback_data="change_rate")],
    ])
    return keyboard


def get_yes_no_keyboard(expense_data: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения расхода"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"expense_yes:{expense_data}"),
            InlineKeyboardButton(text="💬 Добавить комментарий", callback_data=f"expense_comment:{expense_data}")
        ],
        [
            InlineKeyboardButton(text="❌ Нет", callback_data="expense_no")
        ]
    ])
    return keyboard


def get_rate_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения курса"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подходит", callback_data="rate_accept"),
            InlineKeyboardButton(text="✏️ Ввести свой курс", callback_data="rate_manual")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="cancel")]
    ])
    return keyboard


def get_trips_keyboard(trips: List[Dict[str, Any]], active_trip_id: int = None) -> InlineKeyboardMarkup:
    """Клавиатура со списком путешествий"""
    buttons = []
    
    for trip in trips:
        trip_id = trip['trip_id']
        is_active = trip_id == active_trip_id
        
        status_icon = "✅" if is_active else "🔘"
        trip_name = f"{trip['from_country']} → {trip['to_country']}"
        
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {trip_name}", 
                callback_data=f"trip_select:{trip_id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_trip_actions_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с действиями для путешествия"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сделать активным", callback_data=f"trip_activate:{trip_id}")],
        [InlineKeyboardButton(text="💰 Показать баланс", callback_data=f"trip_balance:{trip_id}")],
        [InlineKeyboardButton(text="📊 История расходов", callback_data=f"trip_history:{trip_id}")],
        [InlineKeyboardButton(text="💱 Изменить курс", callback_data=f"trip_rate:{trip_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"trip_delete:{trip_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="my_trips")]
    ])
    return keyboard


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    return keyboard


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
    ])
    return keyboard


def get_confirm_delete_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"trip_delete_confirm:{trip_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"trip_select:{trip_id}")
        ]
    ])
    return keyboard

