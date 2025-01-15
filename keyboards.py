from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


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


# Главная клавиатура для бота
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Показать новое слово")],
            [KeyboardButton(text="Посмотреть изученное")]
        ],
        resize_keyboard=True
    )


# Клавиатура для админ-панели
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Посмотреть всех пользователей")],
            [KeyboardButton(text="Вернуться обратно")]
        ],
        resize_keyboard=True
    )

