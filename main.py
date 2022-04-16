import logging
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from dotenv import dotenv_values

config = dotenv_values(".env")

API_TOKEN = config['BOT_API_KEY']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

markup = ReplyKeyboardMarkup().add(KeyboardButton(text='Отправьте мне свой контакт', request_contact=True))


async def get_phone_info(phone):
    r = requests.get('{0}?phone={1}&token={2}'.format(config['PHONE_CHECK_URL'], phone, config['PHONE_CHECK_TOKEN']))
    return r


async def check_phone_number(phone):
    result = {}
    r = requests.get('https://zniis.ru/bdpn/check/?num={0}'.format(phone[2:]))
    html = r.text
    result['operator'] = html.split('Оператор: ')[1].split('<br>')[0]
    result['region'] = html.split('Регион: ')[1].split('"')[0]
    return result


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer(
        "{1}, бот {0} приветствует вас.\n\n Жмите /new".format(config['BOT_NAME'], message.from_user.first_name))


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
        res = await get_phone_info(message.contact.phone_number)
        await message.answer('Ваш номер телефона: {0}'.format(message.contact.phone_number))
        await message.answer(res.text)
        phone_info = await check_phone_number(message.contact.phone_number)
        await message.answer('{0}\n{1}'.format(phone_info['opertor'],phone_info['region']))
        # await message.answer('Я сейчас позвоню Вам на номер {0}'.format(phonenumber))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
