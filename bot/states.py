"""
FSM States для бота
"""
from aiogram.fsm.state import State, StatesGroup


class TripCreation(StatesGroup):
    """Состояния создания путешествия"""
    waiting_from_country = State()
    waiting_to_country = State()
    waiting_rate_decision = State()
    waiting_manual_rate = State()
    waiting_initial_amount = State()


class RateChange(StatesGroup):
    """Состояния изменения курса"""
    waiting_new_rate = State()


class ExpenseComment(StatesGroup):
    """Состояния комментирования расхода"""
    waiting_comment = State()

