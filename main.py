import logging
import uuid
import random
import re
import pytz
from datetime import datetime
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import dotenv_values

config = dotenv_values("config.env")

API_TOKEN = config['BOT_API_KEY']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# markups
markup = ReplyKeyboardMarkup().add(KeyboardButton(text='Поделиться номером телефона', request_contact=True))
markup_remove = types.ReplyKeyboardRemove()

# debug mode
DEBUG = True

tz = pytz.timezone('Europe/Moscow')


async def get_random():
    vals = []
    for item in range(0, random.randint(4, 6)):
        vals.append(random.randint(1, 5))
    # print(vals)
    res = [str(x) for x in vals]
    s = '-'
    s = s.join(res)
    return s


async def get_code():
    vals = []
    for item in range(0, 4):
        vals.append(random.randint(1, 5))
    # print(vals)
    res = [str(x) for x in vals]
    s = ''
    s = s.join(res)
    return s


async def send_new_call(phone, numbers_str):
    result = {}
    phone = phone.replace('+','')
    json_response = None
    result['status'] = False
    result['message'] = numbers_str
    try:
        req_str = f"""{config['CALL_API_URL']}?phone={phone}&code={numbers_str}&client={phone}&unique={uuid.uuid4()}&voice=true&key={config['CALL_API_KEY']}&service_id={config['CALL_SERVICE_ID']}"""
        response = requests.get(req_str)
        json_response = response.json()
        if DEBUG:
            print(req_str)
            print(json_response)
        result['response'] = json_response
        result['status'] = True
        result['time_sent'] = str(datetime.now(tz)).split('.')[0]
    except Exception as e:
        print(e)
        result['error'] = str(e)
    return result


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer(
        "Приветствую {1}! \nЯ помогу записать видео и подписать его цифровой подписью.\n\n Жмите 👉 /new".format(
            config['BOT_NAME'], message.from_user.first_name))


@dp.message_handler(commands=['new'])
async def send_new(message: types.Message):
    """
    new command
    """
    await message.answer("Мне нужен Ваш контактный номер", reply_markup=markup)


@dp.message_handler(content_types=['contact'])
async def contact(message):
    if message.contact is not None:
        if config['ADMIN_SERVICE_GROUP']:
            service_chatid = config['ADMIN_SERVICE_GROUP']
        else:
            service_chatid = config['ADMIN_CHATID']
        numbers_str = await get_code()
        answ_call = await send_new_call(message.contact.phone_number, numbers_str)

        if answ_call['status']:
            msg_str = """На Ваш номер <b>{0}</b>\n<b>{2}</b> Московского времени был отправлен звонок. 
\n‼️Обязательно покажите цифры <b>{1}</b> пальцами вначале видео""".format(
                message.contact.phone_number,
                answ_call['message'],
                answ_call['time_sent'],
            )
            await message.answer(msg_str, parse_mode=types.ParseMode.HTML, reply_markup=markup_remove)
            await bot.send_message(service_chatid, f"🟢 Info {message.contact.phone_number}:\n\n{str(answ_call)}")
        else:
            await message.answer('Что-то пошло не так. Сервис временно не доступен', reply_markup=markup_remove)
            await bot.send_message(service_chatid, f"⭕️Error {message.contact.phone_number}:\n\n{answ_call['error']}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
