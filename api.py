import asyncio

import requests
from googletrans import Translator

from aiogram import types

from main import logger


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
