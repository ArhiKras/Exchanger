import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from .config import DATABASE_PATH


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            active_trip_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица путешествий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            from_country TEXT NOT NULL,
            to_country TEXT NOT NULL,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            exchange_rate REAL NOT NULL,
            initial_amount_from REAL NOT NULL,
            initial_amount_to REAL NOT NULL,
            current_balance_from REAL NOT NULL,
            current_balance_to REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Таблица расходов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            amount_to REAL NOT NULL,
            amount_from REAL NOT NULL,
            exchange_rate REAL NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trip_id) REFERENCES trips(trip_id)
        )
    """)
    
    conn.commit()
    conn.close()


def get_connection():
    """Получить соединение с БД"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_user(user_id: int, username: str = None, first_name: str = None):
    """Создать или обновить пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (user_id, username, first_name))
    
    conn.commit()
    conn.close()


def create_trip(user_id: int, from_country: str, to_country: str, 
                from_currency: str, to_currency: str, exchange_rate: float,
                initial_amount_from: float, initial_amount_to: float) -> int:
    """Создать новое путешествие"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO trips (user_id, from_country, to_country, from_currency, 
                          to_currency, exchange_rate, initial_amount_from, 
                          initial_amount_to, current_balance_from, current_balance_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, from_country, to_country, from_currency, to_currency, 
          exchange_rate, initial_amount_from, initial_amount_to, 
          initial_amount_from, initial_amount_to))
    
    trip_id = cursor.lastrowid
    
    # Устанавливаем это путешествие как активное
    cursor.execute("UPDATE users SET active_trip_id = ? WHERE user_id = ?", 
                   (trip_id, user_id))
    
    conn.commit()
    conn.close()
    
    return trip_id


def get_user_trips(user_id: int) -> List[Dict[str, Any]]:
    """Получить все путешествия пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC
    """, (user_id,))
    
    trips = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return trips


def get_trip_by_id(trip_id: int) -> Optional[Dict[str, Any]]:
    """Получить путешествие по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM trips WHERE trip_id = ?", (trip_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    return dict(row) if row else None


def get_active_trip(user_id: int) -> Optional[Dict[str, Any]]:
    """Получить активное путешествие пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.* FROM trips t
        JOIN users u ON u.active_trip_id = t.trip_id
        WHERE u.user_id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def set_active_trip(user_id: int, trip_id: int):
    """Установить активное путешествие"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET active_trip_id = ? WHERE user_id = ?", 
                   (trip_id, user_id))
    
    conn.commit()
    conn.close()


def add_expense(trip_id: int, amount_to: float, amount_from: float, 
                exchange_rate: float, description: str = None) -> int:
    """Добавить расход"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Добавляем расход
    cursor.execute("""
        INSERT INTO expenses (trip_id, amount_to, amount_from, exchange_rate, description)
        VALUES (?, ?, ?, ?, ?)
    """, (trip_id, amount_to, amount_from, exchange_rate, description))
    
    expense_id = cursor.lastrowid
    
    # Обновляем баланс путешествия
    cursor.execute("""
        UPDATE trips 
        SET current_balance_to = current_balance_to - ?,
            current_balance_from = current_balance_from - ?
        WHERE trip_id = ?
    """, (amount_to, amount_from, trip_id))
    
    conn.commit()
    conn.close()
    
    return expense_id


def get_trip_expenses(trip_id: int) -> List[Dict[str, Any]]:
    """Получить все расходы путешествия"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM expenses WHERE trip_id = ? ORDER BY created_at DESC
    """, (trip_id,))
    
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return expenses


def update_trip_rate(trip_id: int, new_rate: float):
    """Обновить курс обмена для путешествия"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE trips SET exchange_rate = ? WHERE trip_id = ?
    """, (new_rate, trip_id))
    
    conn.commit()
    conn.close()


def delete_trip(trip_id: int):
    """Удалить путешествие и все его расходы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Удаляем расходы
    cursor.execute("DELETE FROM expenses WHERE trip_id = ?", (trip_id,))
    
    # Удаляем путешествие
    cursor.execute("DELETE FROM trips WHERE trip_id = ?", (trip_id,))
    
    conn.commit()
    conn.close()

