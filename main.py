import time
import logging

from aiogram import Bot, Dispatcher, types, Router, BaseMiddleware
import logging

from aiogram import Bot, Dispatcher, types

from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from aiogram.fsm.storage.memory import MemoryStorage

from commands import handlers

#Enter the token here
TOKEN = ''
ADMIN_ID = 5895319703

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

# Middleware для логирования сообщений
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], event: Message, data: Dict[str, Any]) -> Any:
        logger.info(f"Получено сообщение от {event.from_user.id}: {event.text}")
        return await handler(event, data)


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Инициализация хранилища состояний и диспетчера
storage = MemoryStorage()
bot = Bot(token=TOKEN)  # Создание объекта бота с токеном
dp = Dispatcher(storage=storage)  # Создание объекта диспетчера для маршрутизации сообщений
dp.include_router(handlers.router)  # Создание маршрутизатора для обработки команд

# Регистрация middleware
dp.message.middleware.register(LoggingMiddleware())



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