import logging
import sqlite3
import os
import uuid
import random
import re
import pytz
from datetime import datetime
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text
from telethon.sync import TelegramClient, events
from telethon.tl.types import InputMessagesFilterVideo
from dotenv import dotenv_values
import json
from datetime import datetime
import time
from moviepy.editor import *

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

if config['BOT_ADMIN_SERVICE_GROUP']:
    service_chatid = config['BOT_ADMIN_SERVICE_GROUP']
else:
    service_chatid = config['BOT_ADMIN_CHATID']

sql_init = False

if not os.path.exists('svidetel.db'):
    sql_init = True
conn = sqlite3.connect('svidetel.db')
cur = conn.cursor()

if sql_init:
    with open("migrations/initial_migration.sql", "r") as file:
        mass = file.read()
        for sql_item in mass.split(';'):
            if len(sql_item) > 5:
                cur.execute(sql_item)
                conn.commit()


async def send_to_db(sql):
    cur.execute(sql)
    conn.commit()


async def log_db_add(chatid, msg):
    await send_to_db(
        f"""INSERT INTO log (`chatid`, `message`,`created`) VALUES('{chatid}', '{msg}',datetime('now'));""")


async def get_data(sql):
    result = {}
    result['status'] = False
    try:
        cur.execute(sql)
        conn.commit()
        result['status'] = True
    except Exception as e:
        logging.info('SQL exception get_data(): ' + str(e))
    result['data'] = cur.fetchall()
    return result


async def phone_exists_check(chatid):
    result = {}
    result['status'] = False
    sql = f"""select count(*) from user where chatid = {chatid} and `phone` is not null; """
    try:
        cur.execute(sql)
        conn.commit()
        result['status'] = True
    except Exception as e:
        logging.info('SQL exception get_data(): ' + str(e))

    result['data'] = cur.fetchall()
    return result


def check_video(chatid, local_video_in_file_path, local_video_out_file_path, sec_end):
    result = {}
    result['status'] = False
    result['duration'] = 0
    try:
        video = VideoFileClip(local_video_in_file_path)
        result['duration'] = int(video.duration)
        # sec_end = float(sec_end)
        # if result['duration'] > sec_end:
        #     video = video.subclip(0, sec_end)
        # else:
        #     video = video.subclip(0, result['duration'])
        # result_video = CompositeVideoClip([video])
        # result_video.write_videofile(local_video_out_file_path)
        result['status'] = True
    except Exception as e:
        result['error'] = f'{chatid} \n{local_video_in_file_path}\n\n{str(e)}'
    return result


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


async def send_call(phone, numbers_str):
    result = {}
    json_response = None
    result['status'] = False
    result['message'] = numbers_str
    try:
        url = config["CALL_API_URL"]

        payload = json.dumps([{
            "channelType": "FLASHCALL",
            "senderName": "any sender",
            "destination": phone,
            "content": numbers_str,
        }])
        headers = {
            'Authorization': f'Basic {config["CALL_API_KEY"]}',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        json_response = response.json()
        print(response.status_code)
        if DEBUG:
            print(json_response)
        result['response'] = json_response
        result['status'] = True
        result['time_sent'] = str(datetime.now(tz)).split('.')[0]
    except Exception as e:
        print(e)
        result['error'] = str(e)
    return result


async def send_new_call(phone, numbers_str):
    result = {}
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


async def make_call(message):
    numbers_str = await get_code()
    sql = f"""select phone from user where chatid={message.from_user.id}; """
    sql_result = await get_data(sql)
    # if sql_result != None:
    phone_number = dict(sql_result)['data'][0][0]
    print(phone_number)

    answ_call = await send_call(phone_number, numbers_str)

    if answ_call['status']:
        msg_str = f"""На Ваш номер <b>{phone_number}</b>\n<b>{answ_call['time_sent']}</b> Московского времени был отправлен звонок.
        \n‼️<i>Обязательно поднимите трубку</i> от номера <b>+7-xxx-xxx-{answ_call['message']}</b>.
    \n‼️Обязательно <i>скажите и покажите цифры</i> <b>{answ_call['message']}</b> пальцами на первой минуте видео."""

        await message.answer(msg_str, parse_mode=types.ParseMode.HTML, reply_markup=markup_remove)
        await bot.send_message(service_chatid, f"🟢 Info {phone_number}:\n\n{str(answ_call)}")
    else:
        msg_str = 'Что-то пошло не так. Сервис временно не доступен'
        await message.answer(msg_str, reply_markup=markup_remove)
        await bot.send_message(service_chatid, f"⭕️Error {phone_number}:\n\n{answ_call['error']}")
    await log_db_add(message.from_user.id, f'{msg_str}')


@dp.message_handler(state='*', commands=['start'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await log_db_add(message.from_user.id, message.text)
    await send_to_db(f"""INSERT OR IGNORE INTO USER (`chatid`,`username`,`first_name`,`last_name`,`created`,`upd`) 
        VALUES ('{message.from_user.id}',
        '{message.from_user.username}',
        '{message.from_user.first_name}',
        '{message.from_user.last_name}',
        datetime('now'),datetime('now'));""")

    # upd user info
    await send_to_db(f"""UPDATE USER SET 
        `username` = '{message.from_user.username}',
        `first_name` = '{message.from_user.first_name}',
        `last_name` = '{message.from_user.last_name}',
        `upd` = datetime('now') 
        where `chatid`={message.from_user.id}
    """)

    await message.answer(
        "Приветствую {1}! \nЯ помогу записать видео и подписать его цифровой подписью.\n\n Жмите 👉 /new".format(
            config['BOT_NAME'], message.from_user.first_name))


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    """
    This handler will be called when user sends `/help` command
    """
    await log_db_add(message.from_user.id, message.text)
    await message.answer("Я помогу записать видео и подписать его цифровой подписью.\n\n Жмите 👉 /new")


@dp.message_handler(state='*', commands=['new'])
async def send_new(message: types.Message):
    """
    new command
    """
    await log_db_add(message.from_user.id, message.text)

    if dict(await phone_exists_check(message.from_user.id))['data'][0][0] == 1:
        await make_call(message)
    else:
        await message.answer("Мне нужен Ваш контактный номер", reply_markup=markup)


@dp.message_handler(content_types=['contact'])
async def contact(message):
    if message.contact is not None:
        await send_to_db(f"""UPDATE USER SET 
                               `phone` = '{message.contact.phone_number}',
                               `username` = '{message.from_user.username}',
                               `first_name` = '{message.from_user.first_name}',
                               `last_name` = '{message.from_user.last_name}',
                               `upd` = datetime('now') 
                               where `chatid`={message.from_user.id}
                           """)
        await log_db_add(message.from_user.id, f'Принят контакт пользователя {message.contact.phone_number}')
        await make_call(message)


@dp.message_handler(commands=['id'])
async def show_chat_id(message: types.Message):
    await message.answer(f'Ваш chatid: {message.from_user.id}')


@dp.message_handler(content_types=["video"])
async def download_video(message: types.Message):
    # Printing download progress
    async def download_callback(current, total):
        await user_message.edit_text(text='Обработка видеофайла: {:.0%}'.format(current / total))
        # print('Downloaded', current, 'out of', total,
        #       'bytes: {:.2%}'.format(current / total))

    # Присваиваем значения внутренним переменным
    client_working_status = True
    api_id = config['CLIENT_API_ID']
    api_hash = config['CLIENT_API_HASH']
    username = config['CLIENT_USERNAME']
    # async with TelegramClient('name', api_id, api_hash) as client:
    #     @client.on(events.NewMessage(int(config['BOT_CHATID'])))
    #     async def handler(event):
    #         client_message = event.message
    #         # print(event)
    #         # print(client_message)
    #         # print(client_message.media)
    #         media_file_datetime_str = str(client_message.date).replace('+00:00', '').replace(':', '_').replace(' ', '_')
    #         file_path = f"video/{client_message.message}_{media_file_datetime_str}"
    #         try:
    #             if client_message.media != 'None':
    #                 start_time = datetime.now()
    #                 local_video_in_file_path = await client.download_media(client_message, file=file_path,
    #                                                                        progress_callback=download_callback)
    #                 print(local_video_in_file_path)
    #                 local_video_out_file_path = local_video_in_file_path.replace('.mp4', '_out.mp4')
    #                 video_info = check_video(client_message.message, local_video_in_file_path,
    #                                          local_video_out_file_path,
    #                                          60)
    #                 print(video_info)
    #                 if video_info['status']:
    #                     await user_message.edit_text(text=f'Готово! Обработано за {(datetime.now() - start_time)} сек.')
    #                     await bot.send_video(message.from_user.id,
    #                                          caption=f"Данный видеофайл подписан цифровой подписью (продолжительность: {video_info['duration']}) сек.",
    #                                          video=message.video.file_id)
    #
    #         except Exception as e:
    #             print(e)
    #         finally:
    #             client_working_status = False
    #
    #     # await bot.forward_message('1982252518',message.from_user.id,message.message_id)

    user_message = await message.reply(
        f'Обработка видеофайла. Это может занять продолжительное время. Я напишу, как будет готово.')
    print(message.video)
    caption_str = str(
        {
            'chatid': message.from_user.id,
            'message_id': user_message.message_id,
            'message_video_file_id':message.video.file_id,
        }
    )
    await bot.send_video(config['CLIENT_CHAT_ID'], caption=caption_str, video=message.video.file_id)
    # user_message = await message.answer(
    #     'Обработка видеофайла. Это может занять продолжительное время. Я напишу, как будет готово.')
    # if client_working_status:
    #     await client.run_until_disconnected()

    # file_id = message.video.file_id  # Get file id
    # file = await bot.get_file(file_id)  # Get file path
    # print(file)
    # unique_index = uuid.uuid4()
    # telegram_file_path = file.file_path
    # local_video_in_file_path = f"video/{message.from_user.id}_{unique_index}.mp4"
    # local_video_out_file_path = f"video/{message.from_user.id}_{unique_index}_out.mp4"
    # await bot.download_file(telegram_file_path, local_video_in_file_path)
    # video_info = await check_video(message.from_user.id, local_video_in_file_path, local_video_out_file_path,
    #                                config['VIDEO_DURATION_CHECK'])
    # if video_info['status']:
    #     await log_db_add(message.from_user.id,
    #                      f'Принято видео от пользователя продолжительностью {video_info["duration"]} сек.')
    #     await message.answer(f"Видео на {video_info['duration']} сек")
    #     await bot.send_video(message.from_user.id, open(local_video_out_file_path, 'rb'))
    # else:
    #     await bot.send_message(service_chatid, video_info['error'])
    #     await log_db_add(log_db_addmessage.from_user.id, f'Ошибка анализа видео от пользователя {video_info["error"]}')


@dp.message_handler()
async def send_forward(message: types.Message):
    """
    forwarder bot to user
    """
    # await log_db_add(message.from_user.id, message.text)
    if message.from_user.id == int(config['CLIENT_CHAT_ID']):
        client_user_info = eval(message.text)
        await bot.edit_message_text(chat_id=int(client_user_info['chatid']),
                                    message_id=int(client_user_info['message_id']), text=client_user_info['text'])
        if 'Готово!' in client_user_info['text']:
            if os.system(f"/opt/cprocsp/bin/amd64/cryptcp -sign -detach '/{client_user_info['local_video_in_file_path']}' '/{client_user_info['local_video_in_file_path']}.sig'"):
                await bot.send_video(int(client_user_info['chatid']),
                                     caption=f"Готовим цифровую подпись к этому видео.",
                                     video=client_user_info[message.video.file_id])
                await bot.send_document(int(client_user_info['chatid']), open(f"{client_user_info['local_video_in_file_path']}.sig", 'rb'),
                caption = f"Цифровая подпись к видео",
                )




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
