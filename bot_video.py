
import os
import asyncio
from aiogram import Bot, Dispatcher, types, executor
import subprocess

bot_token = '7013690800:AAG8UX5dpYlm--Fc5PsqhiNsigFTcvnNir8C'

bot = Bot(token=bot_token)
dp = Dispatcher(bot)



async def download_video(message: types.Message):
    video = message.video
    file_info = await bot.get_file(video.file_id)
    file_path = file_info.file_path
    file_extension = os.path.splitext(file_path)[1]
    new_file_name = f"demo.mp4"
    await bot.download_file(file_path, new_file_name)
    await message.answer("Видео сохранено")
    result = subprocess.run(['python', 'video_demo.py', '-c', 'config.json', 'demo.mp4'], stdout=subprocess.PIPE)
    await message.answer(result.stdout.decode('cp1251', errors='ignore'))


async def download_round_video(message: types.Message):
    video = message.video_note
    file_info = await bot.get_file(video.file_id)
    file_path = file_info.file_path
    file_extension = os.path.splitext(file_path)[1]
    new_file_name = f"demo.mp4"
    await bot.download_file(file_path, new_file_name)
    await message.answer("Видео сохранено")
    result = subprocess.run(['python', 'video_demo.py', '-c', 'config.json', 'demo.mp4'], stdout=subprocess.PIPE)
    await message.answer(result.stdout.decode('cp1251', errors='ignore'))


dp.register_message_handler(download_video, content_types=types.ContentType.VIDEO)
dp.register_message_handler(download_round_video, content_types=types.ContentType.VIDEO_NOTE)

if __name__ == '__main__':
    executor.start_polling(dp)
    
