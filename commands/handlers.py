import sqlite3

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from api import get_random_word
from database.database import create_users_table, show_all_users, connect_db, create_table
from keyboards import get_main_keyboard, get_admin_keyboard, get_word_keyboard, get_studied_words_keyboard
from main import logger, ADMIN_ID
from states import Form

from callbacks import CallbackFactory

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Я помогу тебе изучать новые английские слова. Выбери действие:",
                         reply_markup=get_main_keyboard())

    # Добавляем пользователя в базу данных
    username = message.from_user.username if message.from_user.username else str(message.from_user.id)
    conn = sqlite3.connect("users.db")
    create_users_table(conn)  # Создаем таблицу без пересоздания
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Ошибка добавления пользователя в базу данных: {e}")
    finally:
        conn.close()

# Функция для проверки, является ли пользователь администратором
def is_admin(user_id):
    return user_id == ADMIN_ID

# Команда для админ-панели
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if is_admin(message.from_user.id):
        await message.answer("Добро пожаловать в админ-панель! Выберите действие:",
                             reply_markup=get_admin_keyboard())
    else:
        await message.answer("У вас нет доступа к админ-панели.")


# Обработчик нажатий на кнопки админ-панели
@router.message(
    lambda message: message.text in ["Посмотреть всех пользователей", "Вернуться обратно"])
async def handle_admin_actions(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой команде.")
        return

    if message.text == "Посмотреть всех пользователей":
        await show_all_users(message)
    elif message.text == "Вернуться обратно":
        await message.answer("Вы вернулись в главное меню.", reply_markup=get_main_keyboard())


# Показать новое слово
@router.message(lambda message: message.text == "Показать новое слово")
async def show_new_word(message: types.Message, state: FSMContext):
    await state.set_state(Form.waiting_for_word)

    word, phonetic, translations = await get_random_word(message)
    if word and translations:
        await state.update_data(word=word, translation=translations[0])
        await message.answer(f"Слово: {word}\nТранскрипция: {phonetic}\nПереводы:\n{translations[0]}",
                             reply_markup=get_word_keyboard())
    else:
        await message.answer("Не удалось получить новое слово. Попробуйте позже.")

# Обработчик нажатий на инлайн-кнопки
@router.callback_query(lambda c: c.data in ["save_word", "continue"])
async def process_word_action(callback_query: types.CallbackQuery, state: FSMContext):
    factory = CallbackFactory(state)

    if callback_query.data == "save_word":
        await factory.save_word(callback_query)
    elif callback_query.data == "continue":
        await factory.continue_word(callback_query)

# Посмотреть изученные слова
@router.message(lambda message: message.text == "Посмотреть изученное")
async def show_studied_words(message: types.Message):
    user_id = message.from_user.id  # Получаем user_id

    # Подключаемся к базе данных для пользователя
    conn = connect_db(user_id)
    create_table(conn)  # Убедитесь, что таблица создается
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT word, translation FROM words WHERE user_id = ?", (user_id,))
        words = cursor.fetchall()

        if not words:
            await message.answer("Вы пока не изучали слов.")
        else:
            await message.answer("Вот ваши изученные слова:")
            for word in words:
                await message.answer(f"{word[0]} - {word[1]}")

        await message.answer("Выберите действие:", reply_markup=get_studied_words_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при получении изученных слов для пользователя {user_id}: {e}")
        await message.answer("Произошла ошибка при получении ваших изученных слов. Попробуйте позже.")
    finally:
        conn.close()  # Закрываем соединение с базой данных

# Обработчик нажатий на кнопки управления сохраненными словами
@router.message(lambda message: message.text in ["Очистить сохраненное", "Вернуться назад"])
async def handle_studied_words_action(message: types.Message):
    user_id = message.from_user.id  # Получаем user_id

    if message.text == "Очистить сохраненное":
        # Подключаемся к базе данных для пользователя
        conn = connect_db(user_id)
        create_table(conn)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM words")  # Удаляем слова только для текущего пользователя
        conn.commit()
        await message.answer("Все сохраненные слова были удалены.")
        conn.close()
    elif message.text == "Вернуться назад":
        await message.answer("Вы вернулись в главное меню.", reply_markup=get_main_keyboard())


