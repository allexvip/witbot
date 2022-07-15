from dotenv import dotenv_values
import logging
from telethon.sync import TelegramClient, events
from telethon.tl.types import InputMessagesFilterVideo
from moviepy.editor import *

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
    @client.on(events.NewMessage())
    async def handler(event):
        message = event.message
        print(event)
        print(message)
        print(message.media)
        media_file_datetime_str = str(message.date).replace('+00:00', '').replace(':', '_').replace(' ', '_')
        file_path = f"video/{message.message}_{media_file_datetime_str}"
        try:
            if message.media != 'None':
                local_video_in_file_path = await client.download_media(message, file=file_path,
                                                                       progress_callback=callback)
                print(local_video_in_file_path)
                local_video_out_file_path = local_video_in_file_path.replace('.mp4', '_out.mp4')
                video_info = await check_video(message.message, local_video_in_file_path, local_video_out_file_path, 60)
        except Exception as e:
            pass


    client.run_until_disconnected()
