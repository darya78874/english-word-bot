# Создание класса состояний
from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    waiting_for_word = State()  # Ожидание слова от пользователя
