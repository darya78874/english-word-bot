# Фабрика коллбэков
from aiogram.fsm.context import FSMContext

from commands.handlers import show_new_word
from database.database import connect_db, create_table
from aiogram import types

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

