import os

from dotenv import dotenv_values
import logging
from telethon.sync import TelegramClient, events
from telethon.tl.types import InputMessagesFilterVideo
from moviepy.editor import *
import asyncio
import datetime
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

# Считываем учетные данные
config = dotenv_values("config.env")

API_TOKEN = config['BOT_API_KEY']

# Присваиваем значения внутренним переменным
api_id = config['CLIENT_API_ID']
api_hash = config['CLIENT_API_HASH']
username = config['CLIENT_USERNAME']


async def check_video(chatid, local_video_in_file_path, local_video_out_file_path, sec_end):
    result = {}
    result['status'] = False
    result['duration'] = 0
    try:
        video = VideoFileClip(local_video_in_file_path)
        result['duration'] = float(video.duration)
        sec_end = float(sec_end)
        if result['duration'] > sec_end:
            video = video.subclip(0, sec_end)
        else:
            video = video.subclip(0, result['duration'])
        result_video = CompositeVideoClip([video])
        result_video.write_videofile(local_video_out_file_path)
        result['status'] = True
    except Exception as e:
        result['error'] = f'{chatid} \n{local_video_in_file_path}\n\n{str(e)}'
    return result


with TelegramClient('name', api_id, api_hash) as client:
    @client.on(events.NewMessage(int(config['BOT_CHATID'])))
    async def handler(event):
        #if event.video:
        message = event.message
        bot_user_info = eval(message.message)
        bot_user_info['text'] = ''
        async def download_callback(current, total):
            await asyncio.sleep(int(config['CLIENT_PROCESSING_NOTIFY_PERIOD_SEC']))
            procent_val = round(100*current / total,1)
            bot_user_info['text'] = f'Обработка видеофайла. {procent_val}%'
            await client.send_message(int(config['BOT_CHATID']),str(bot_user_info))


        media_file_datetime_str = str(message.date).replace('+00:00', '').replace(':', '_').replace(' ', '_')
        file_path = f"video/{bot_user_info['chatid']}_{media_file_datetime_str}"
        try:
            if message.media != 'None':
                local_video_in_file_path = await client.download_media(message, file=file_path,
                                                                       progress_callback=download_callback)
                bot_user_info['local_video_in_file_path'] = local_video_in_file_path
                bot_user_info['text'] = f'Готово! Обработано за  сек.'
                await client.send_message(int(config['BOT_CHATID']), str(bot_user_info))
                print(local_video_in_file_path)
                # local_video_out_file_path = local_video_in_file_path.replace('.mp4', '_out.mp4')
                # start_time = datetime.now()
                # video_info = await check_video(bot_user_info['chatid'], local_video_in_file_path, local_video_out_file_path,
                #                                60)
                #
                #
                # if video_info['status']:
                #     bot_user_info['text'] = f'Готово! Обработано за  сек.'
                #
                #     await client.send_message(int(config['BOT_CHATID']), str(bot_user_info))
                # else:
                #     await client.send_message(int(config['BOT_CHATID']), video_info['error'])
                #     #await log_db_add(log_db_addmessage.from_user.id, f'Ошибка анализа видео от пользователя {video_info["error"]}')


        except Exception as e:
            pass


    client.run_until_disconnected()
