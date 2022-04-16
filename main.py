import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import dotenv_values

config = dotenv_values(".env")

API_TOKEN = config['BOT_API_KEY']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

markup = ReplyKeyboardMarkup().add(KeyboardButton(text='Отправьте мне свой контакт',request_contact=True))

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer("{1}, бот {0} приветствует вас.\n\n Жмите /new".format(config['BOT_NAME'],message.from_user.first_name))

@dp.message_handler(commands=['new'])
async def send_new(message: types.Message):
    """
    new command
    """
    await message.answer("Пожалуйста предоставьте боту свой номер телефона", reply_markup=markup)

@dp.message_handler(content_types=['contact'])
async def contact(message):
    if message.contact is not None:
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(message.chat.id, 'Вы успешно отправили свой номер', reply_markup=markup)
        global phonenumber
        phonenumber = str(message.contact.phone_number)
        user_id = str(message.contact.user_id)
        await message.answer('Ваш номер телефона: {0}'.format(phonenumber))
        await message.answer('Я сейчас позвоню Вам на номер {0}'.format(phonenumber))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
