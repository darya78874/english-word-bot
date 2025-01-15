import sqlite3

from aiogram import types


# Создаем таблицу пользователей (без удаления данных)
def create_users_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE
    )''')
    conn.commit()

# Создаем таблицу для слов
def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        word TEXT NOT NULL,
        translation TEXT NOT NULL
    )''')
    conn.commit()



# Функция для показа всех пользователей
async def show_all_users(message: types.Message):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()

    if not users:
        await message.answer("Нет зарегистрированных пользователей.")
    else:
        user_list = "\n".join([f"@{user[0]}" for user in users])  # Добавляем "@" перед username
        await message.answer(f"Список всех пользователей:\n{user_list}")

    conn.close()



# Функция для подключения к базе данных для пользователя
def connect_db(username):
    db_name = "words.db"  # Используем одну базу данных для всех пользователей
    conn = sqlite3.connect(db_name)
    return conn