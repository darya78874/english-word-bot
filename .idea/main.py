import sqlite3
import logging
import requests
from googletrans import Translator

from aiogram import Bot, Dispatcher, types
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

# Middleware для логирования сообщений
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]) -> Any:
        logger.info(f"Получено сообщение от {event.from_user.id}: {event.text}")
        return await handler(event, data)


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваш токен бота
API_TOKEN = '6820913280:AAF6VPUtzE9WahZZ20Z7Id7cw-Yafvrmv7U'
ADMIN_ID = 5683830332

# Инициализация хранилища состояний и диспетчера
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)  # Создание объекта бота с токеном
dp = Dispatcher(storage=storage)  # Создание объекта диспетчера для маршрутизации сообщений
router = Router()  # Создание маршрутизатора для обработки команд

# Регистрация middleware
dp.message.middleware.register(LoggingMiddleware())

# Создание класса состояний
class Form(StatesGroup):
    waiting_for_word = State()  # Ожидание слова от пользователя

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

# Главная клавиатура для бота
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Показать новое слово")],
            [KeyboardButton(text="Посмотреть изученное")]
        ],
        resize_keyboard=True
    )

# Инлайн клавиатура для сохранения слова
def get_word_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сохранить", callback_data="save_word"),
                InlineKeyboardButton(text="Продолжить", callback_data="continue")
            ]
        ]
    )

# Клавиатура для управления сохраненными словами
def get_studied_words_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Очистить сохраненное")],
            [KeyboardButton(text="Вернуться назад")]
        ],
        resize_keyboard=True
    )

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

# Клавиатура для админ-панели
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Посмотреть всех пользователей")],
            [KeyboardButton(text="Вернуться обратно")]
        ],
        resize_keyboard=True
    )

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


# Функция для проверки валидности слова
def is_valid_word(word):
    return word.isalpha() and len(word) > 1

# Функция для получения определений слова
def get_definitions(word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            meanings = data[0].get('meanings', [])
            phonetic = data[0].get('phonetics', [{}])[0].get('text', '')
            return phonetic, meanings
    except requests.exceptions.HTTPError as e:
        logger.warning(f"Ошибка при получении определений для слова '{word}': {e}")
    except Exception as e:
        logger.error(f"Ошибка при получении определений для слова '{word}': {e}")
    return None, []

# Функция для перевода определений
async def translate_definitions(definitions):
    if not definitions:
        return []

    translations = []
    translator = Translator()

    for meaning in definitions:
        for definition in meaning.get('definitions', []):
            try:
                translated = await translator.translate(definition.get('definition', ''), src='en', dest='ru')
                translations.append(translated.text)
            except Exception as e:
                logger.error(f"Ошибка при переводе определения: {e}")
                translations.append(definition.get('definition', ''))

    return translations

# Функция для получения случайного слова
async def get_random_word(message: types.Message):
    search_message = await message.answer("Ищем для вас подходящее слово...")
    while True:
        try:
            response = requests.get("https://random-word-api.herokuapp.com/word?number=1")
            response.raise_for_status()
            word_data = response.json()
            if word_data:
                word = word_data[0]
                if is_valid_word(word):
                    phonetic, meanings = get_definitions(word)
                    if meanings:
                        translations = await translate_definitions(meanings)
                        await message.bot.delete_message(chat_id=message.chat.id, message_id=search_message.message_id)
                        return word, phonetic, translations

        except Exception as e:
            logger.error(f"Ошибка при получении случайного слова: {e}")
            await message.answer("Произошла ошибка, попробуйте позже.")
        await asyncio.sleep(1)


# Функция для подключения к базе данных для пользователя
def connect_db(username):
    db_name = "words.db"  # Используем одну базу данных для всех пользователей
    conn = sqlite3.connect(db_name)
    return conn

# Фабрика коллбэков
class CallbackFactory:
    def __init__(self, state: FSMContext):
        self.state = state

    async def save_word(self, callback_query: types.CallbackQuery):
        word_data = await self.state.get_data()
        word = word_data.get("word")
        translation = word_data.get("translation")
        user_id = callback_query.from_user.id

        conn = connect_db(user_id)
        create_table(conn)
        cursor = conn.cursor()

        if word and translation:
            cursor.execute("INSERT INTO words (user_id, word, translation) VALUES (?, ?, ?)",
                           (user_id, word, translation))
            conn.commit()
            await callback_query.answer("Слово сохранено!")
        else:
            await callback_query.answer("Ошибка: слово или перевод отсутствуют.")

        conn.close()

    async def continue_word(self, callback_query: types.CallbackQuery):
        await callback_query.answer("Слово не сохранено.")
        await show_new_word(callback_query.message, self.state)

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

# Регистрация маршрутизатора
dp.include_router(router)

# Запуск бота
async def main():
    await bot.delete_webhook()
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            await asyncio.sleep(5)

if __name__ == '__main__':
    import asyncio

    asyncio.run(main())  # Запускаем основную функцию