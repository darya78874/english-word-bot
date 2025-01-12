import time
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

#Enter the token here
TOKEN = ':)'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

MSG = 'Do you studied English today, {}?'

@dp.message(Command('start'))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name
    logging.info(f'{user_id=} {user_full_name=} {time.asctime()=}')

    await message.reply(f'Hello, {user_full_name}')

    for i in range(7):
        time.sleep(60*60*24)
        await bot.send_message(user_id, MSG.format(user_name))


if __name__ == '__main__':
    dp.start_polling()