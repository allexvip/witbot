import logging

from aiogram import Bot, Dispatcher, executor, types
from dotenv import dotenv_values

config = dotenv_values(".env")

API_TOKEN = config['BOT_API_KEY']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Бот {0} приветствует вас.".format(config['BOT_NAME']))

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)