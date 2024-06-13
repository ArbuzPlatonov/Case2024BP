import os
import asyncio
from aiogram import Bot, Dispatcher, types, executor
from googletrans import Translator, LANGUAGES
import subprocess
import json
from gtts import gTTS
import pymorphy3
morph = pymorphy3.MorphAnalyzer()
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Define state for feedback
class Form(StatesGroup):
    feedback = State()
    
bot_token = "7013690800:AAG8UX5dpYlm--Fc5PsqhiNsigFTcvnNir8"
langchose = "ru"
bot = Bot(token=bot_token)

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

user_languages = {}
user_settings = {}

Bot.set_current(bot)
semaphore = asyncio.Semaphore(2)  # контролирует количество одновременных операций
translator = Translator()
def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = ["Выбор языка перевода 🏳️", "Помощь ❓", "Обратная связь ✉️"]
    keyboard.add(*buttons)
    return keyboard

# Start command handler
@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    keyboard = get_start_keyboard()
    await message.answer("Привет! 👋 \n \nЯ бот для перевода русского жестового языка с видео при помощи ИИ! 🧠 \n \nОтправь мне видеосоощение (кружок или видео) и я переведу жесты в текст или голос! 📟 \n \nВыбор языка - язык на который переводить жесты (по умолчанию русский) 🇷🇺 \n \nПомощь - техническая поддержка бота, обращайтесь туда по любому интересующему вас вопросу ❓  \n \n/settings - настройки результата обработки ⚙️", reply_markup=keyboard)

# Handlers for each button option
@dp.message_handler(lambda message: message.text == "Обратная связь ✉️", state='*')
async def feedback_start(message: types.Message):
    await Form.feedback.set()
    await message.answer("Пожалуйста, напишите ваш отзыв.")

@dp.message_handler(state=Form.feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    # Сохраняем обратную связь в текстовый документ
    with open('feedback.txt', 'a', encoding='utf-8') as file:
        file.write(f"UserID {message.from_user.id}: {message.text}\n")

    # Уведомляем пользователя, что его отзыв был записан
    await message.answer("Спасибо за ваш отзыв!")

    # Сбрасываем состояние, чтобы пользователь мог отправить другие сообщения
    await state.finish()
    
    
@dp.message_handler(lambda message: message.text == "Выбор языка перевода 🏳️")
async def choose_language_handler(message: types.Message):
    # Implement language selection functionality here
    await message.answer("Вы выбрали выбор языка. Пожалуйста, выберите язык.")
    # Создаем кнопки выбора языка
    lang_keyboard = InlineKeyboardMarkup(row_width=2)
    lang_keyboard.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="ru"),
        InlineKeyboardButton("🇺🇸 English", callback_data="en"),
        InlineKeyboardButton("🇮🇳 India", callback_data="hi"),
        InlineKeyboardButton("🇦🇪 Arabic", callback_data="ar"),
        InlineKeyboardButton("🇩🇪 Deutsch", callback_data="de"),
        InlineKeyboardButton("🇨🇳 中文", callback_data="zh-cn"),
    )

    # Отправляем сообщение с кнопками выбора языка
    await message.answer("Выберите язык:", reply_markup=lang_keyboard)


def set_user_language(user_id, lang_choice):
    user_languages[user_id] = lang_choice
    
@dp.callback_query_handler(lambda c: c.data in ["ru", "en", "hi", "ar", "de", "zh-cn"])
async def process_language_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang_choice = callback_query.data

    # Сохраняем язык в отдельном словаре для каждого пользователя
    set_user_language(user_id, lang_choice)

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 
                           f"Вы выбрали язык: {LANGUAGES.get(lang_choice, lang_choice)}")

     
@dp.message_handler(lambda message: message.text == "Помощь ❓")
async def help_handler(message: types.Message):
    # Implement help functionality here
    await message.answer("Напишите нам с вашими предложениями! \n \nТехническая поддержка - @Rayni777")

# Функция для получения настроек пользователя
def get_user_settings(user_id): 
    # Если настройки не установлены, возвращаем по умолчанию 'both'
    return user_settings.get(user_id, 'both')

# Команда настроек
@dp.message_handler(commands=['settings'])
async def command_settings(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    # Кнопки со значениями 'text', 'audio', 'both'
    keyboard.add(InlineKeyboardButton("Только текст", callback_data='set_text'))
    keyboard.add(InlineKeyboardButton("Только аудио", callback_data='set_audio'))
    keyboard.add(InlineKeyboardButton("Текст и аудио", callback_data='set_both'))
    await message.answer("Выберите, что вы хотите получать по умолчанию:", reply_markup=keyboard)

# Обработчик кнопок настроек
@dp.callback_query_handler(lambda c: c.data in ['set_text', 'set_audio', 'set_both'])
async def callback_settings(call: types.CallbackQuery):
    # Установка настроек пользователя
    user_id = call.from_user.id
    user_settings[user_id] = call.data.split('_')[1]  # Устанавливаем настройку (text, audio, both)
    await call.message.answer(f"Настройки обновлены: {user_settings[user_id]}")

# Используем сохраненные настройки пользователя при обработке видео
@dp.callback_query_handler(lambda call: call.data in ['text', 'audio', 'both'])
async def query_handler(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_setting = get_user_settings(user_id)  # Получаем настройки для пользователя
    if user_setting in ['text', 'both']:
        await bot.send_message(chat_id=call.message.chat.id, text=context['text'], reply_to_message_id=call.message.message_id)
    if user_setting in ['audio', 'both']:
        audio_file = context['audio_file']
        if audio_file:
            with open(audio_file, 'rb') as audio:
                await bot.send_voice(chat_id=call.message.chat.id, voice=audio, caption="Ваш текст в аудиоформате", reply_to_message_id=call.message.message_id)
            os.remove(audio_file)
    
    # Убираем клавиатуру после выбора
    await call.message.edit_reply_markup()

# Добавляем команду /settings в обработчик сообщений
dp.register_message_handler(command_settings, commands=['settings'])


@dp.callback_query_handler(lambda c: c.data in ["ru", "en", "hi", "ar", "de", "zh-cn"])
async def process_language_selection(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang_choice = callback_query.data

    # Сохраняем выбранный язык в словарь пользователей, используя user_id в качестве ключа.
    user_languages[user_id] = lang_choice

    # Отправляем сообщение о том, что язык выбран.
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Вы выбрали язык: {LANGUAGES.get(lang_choice, lang_choice)}")

# Заменяем глобальную переменную langchose на функцию, которая получает пользовательский язык
def get_user_language(user_id):
    return user_languages.get(user_id, "ru")  # Возвращаем выбранный язык или "ru" по умолчанию

# Далее используем функцию get_user_language(user_id) вместо глобальной переменной langchose
# Например, в функции video_worker меняем langchose на get_user_language(message.from_user.id)

d_1 = {'ноль': 0, 'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8,
        'девять': 9, 'десять': 10, 'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
        'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18, 'девятнадцать': 19, 'двадцать': 20,
        'тридцать': 30, 'сорок': 40, 'пятьдесят': 50, 'шестьдесят': 60, 'семьдесят': 70,'восемьдесят': 80, 'дявяносто': 90, 
        'сто': 100, 'двести': 200, 'триста': 300, 'четыреста': 400, 'пятьсот': 500, 'шестьсот': 600, 'семьсот': 700,
        'восемьсот': 800, 'девятьсот': 900, 'тысяча': 10**3, 'миллион': 10**6, 'миллиард': 10**9}
d = list(d_1.keys())

def preob(ch):
    s = list(map(int, ch.split()))
    k = 0
    h = []
    a = 0
    for i in range(len(s)):
        if (i<len(s)-1) and ((s[i]<s[i+1]<1000) or (0<=s[i+1]<=19 and 0<=s[i]<=19) or (20<=s[i+1]<=90 and 20<=s[i]<=90) or (100<=s[i+1]<=900 and 100<=s[i]<=900) or (1000<=s[i+1] and 1000<=s[i])):
            if s[i] < 1000:
                h.append(k + a + s[i])
            else:
                h.append(k + a * s[i])
            k = 0
            a = 0
        elif 0<=s[i]<=900:
            a += s[i]
        else:
            k += a*s[i]
            a =0
        if i == len(s)-1:
            h.append(k + a)
    return h

def prenad(sl):
    if {'plur'} in morph.parse(sl[0])[0].tag:
        a = (morph.parse('пренадлежащий')[0].inflect({'plur'}).word())
        b = (morph.parse(sl[1])[0].inflect({'datv'}).word())
                                          
        return sl[0] + a + b
    if morph.parse(sl[0])[0].tag.person not in ['1per', '2per']:
        gen = morph.parse(sl[0])[0].tag.gender
    else:
        gen = 'masc'
    out = sl[0] + ', ' + (morph.parse('пренадлежащий')[0].inflect({gen}).word) + ' ' + (morph.parse(sl[1])[0].inflect({'datv'}).word)
    return out                                                                                

def mini_encoder(out):
    out = out.split()
    
    k = (1 if len(out)>1 else 0)
    
    for i in range(k, len(out)):
        if '/' in out[i]:
            out[i] = out[i][:out[i].find('/')]
        
        if out[i] == 'он/она/они':
            out[i] = 'он'
            
        if ';' in out[i]:
            j = out[i].index(';')
            out[i] = out[i][:j]
        if '(' in out[i]:
            j = out[i].index('(')
            out[i] = out[i][j + 1: -1]
            
        if out[i] in ['что', 'кто', 'где', 'когда', 'откуда', 'зачем', 'почему', 'куда']:
            out[i] += '?'
        
        if out[i] == 'не' or out[i] == 'нет':
            out[i - 1], out[i] = out[i], out[i - 1]
            
        if out[i] == 'мой' or out[i] == 'свой':
            out[i - 1], out[i] = out[i], out[i - 1]
            
        if ({'ADJF'} in morph.parse(out[i])[0].tag) and (({'NOUN'} in morph.parse(out[i-1])[0].tag)) and (out[i] not in ['мой', 'свой', 'твой']):
            out[i - 1], out[i] = out[i], out[i - 1]  
            
        if (out[i - 1] in ['мать', 'мама'] and out[i] in ['отец', 'папа']) or (out[i - 1] in ['мать', 'мама'] and out[i] in ['отец', 'папа']):
            out[i - 1], out[i] = '', 'родители'
            
        if out[i] == 'много':
            out[i-1], out[i] = '', morph.parse(out[i-1])[0].inflect({'plur'}).word
        
        if out[i] == 'MakDonalds':
            out[i] = 'Вкусно и точка'
        
        if (out[i] in ['ради','твой', 'принадлежать']):
            j = i
            while out[j - 2] == '':
                j -= 1
            out[i] = prenad([out[j - 2], out[i - 1], out[i]]) + ('' if i == len(out) - 1 else ',')
            out[j - 2], out[i - 1] = '', ''
            
        if out[i] in ['готов', 'законченно', 'закончить'] and\
        (({'VERB'} in morph.parse(out[i - 1])[0].tag) or ({'INFN'} in morph.parse(out[i - 1])[0].tag)):
            gen = 'masc' if morph.parse(out[i - 2])[0].tag.gender == None else morph.parse(out[i - 2])[0].tag.gender
            out[i] = morph.parse(out[i-1])[0].inflect({'VERB', 'past', gen}).word
            out[i - 1] = ''
            
        if out[i] in ['рано'] and\
        (({'VERB'} in morph.parse(out[i - 1])[0].tag) or ({'INFN'} in morph.parse(out[i - 1])[0].tag)):
            gen = 'masc' if morph.parse(out[i - 2])[0].tag.gender == None else morph.parse(out[i - 2])[0].tag.gender
            out[i] = 'ещё не ' + morph.parse(out[i-1])[0].inflect({'VERB', 'past', gen}).word
            out[i - 1] = ''
                
        if out[i] in d:
            a = ''
            j = i
            while out[j] in d:
                a += str(d_1[out[j]])
                out[j] = ''
                if j == len(out) - 1:
                    break
                j += 1
            num = preob(a)
            if len(num) == 1 and i > 0:                
                out[j] = morph.parse(out[i-1])[0].make_agree_with_number(num[0]).word
                out[i-1] = num[0]
            else:
                for p in num:
                    out[j] = p
            
    fin = ''
    for i in out:
        if i != '':
            fin += str(i) + ' '
    return fin

                                             
async def video_worker():
    while True:
        message, video_path = await queue.get()
        user_id = message.from_user.id
        async with semaphore:
            try:
                process = await asyncio.create_subprocess_exec(
                    'python', 'video_demo.py', '-c', 'config.json', video_path,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if stderr:
                    print(f"Errors: {stderr.decode()}")

                stdout_data = stdout.decode('cp1251').strip()
                raw_results_list = stdout_data.strip('[]').split("', '")
                results_list = [word.strip("'") for word in raw_results_list if word.strip("'").lower() != "нет жеста"]

                if not results_list:
                    await message.answer("Жесты не обнаружены.")
                    return

                words = ' '.join(results_list).split()
                cleaned_words = [words[i] for i in range(len(words)) if i == 0 or words[i] != words[i-1]]
                clean_result = ' '.join(cleaned_words)

                result_in_english = translator.translate(clean_result, src='ru', dest='en').text
                result_finally = translator.translate(result_in_english, src='en', dest=get_user_language(user_id)).text

                context = {'text': mini_encoder(result_finally), 'audio_file': None}

                user_setting = get_user_settings(message.from_user.id)

                if user_setting in ['text', 'both']:
                    await message.answer(context['text'])

                if user_setting in ['audio', 'both']:
                    tts = gTTS(text=context['text'], lang=get_user_language(user_id))
                    audio_file = f'audio_{message.message_id}.mp3'
                    tts.save(audio_file)
                    if os.path.exists(audio_file):  # Проверка существования файла перед отправкой
                        with open(audio_file, 'rb') as audio:
                            await bot.send_voice(chat_id=message.chat.id, voice=audio, caption="Ваш текст в аудиоформате", reply_to_message_id=message.message_id)
                        # Попытка удалить файл после его отправки
                        try:
                            os.remove(audio_file)
                        except OSError as e:
                            print(f"Error: {e.strerror}")


                # Записываем результат распознавания и рейтинг в файл
                with open("results.txt", "a") as file:
                    file.write(f"User ID: {user_id}\n")
                    file.write(f"Result: {context['text']}\n")
                    file.write("Rating: ")

                rating_keyboard = InlineKeyboardMarkup(row_width=5)
                rating_buttons = [InlineKeyboardButton(text=f"{i}⭐️", callback_data=f"rating_{i}") for i in range(1, 6)]
                rating_keyboard.add(*rating_buttons)
                await message.answer("Оцените результат распознавания:", reply_markup=rating_keyboard)

            except subprocess.CalledProcessError as e:
                # Handle the subprocess error. No task_done() call here.
                await message.answer("Ошибка при обработке видео.")
                print(str(e))
            except Exception as e:
                # Handle other exceptions. No task_done() call here.
                await message.answer("На видео жесты не обнаружены.")
                print(str(e))
            finally:
                if os.path.exists(video_path):
                    os.remove(video_path)

            # The single task_done() call for the task just processed.
            queue.task_done()


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('rating'))
async def process_callback_rating(callback_query: types.CallbackQuery):
    # Extract the rating from the callback data
    rating = callback_query.data.split("_")[1]
    
    # Respond to the callback query to acknowledge it (required by Telegram API)
    await bot.answer_callback_query(callback_query.id)
    
    # Write the rating to the file
    with open('results.txt', 'a') as file:
        file.write(f"Rating: {rating}\n")

    # Edit the original message to remove the inline keyboard
    await callback_query.message.edit_text(
        f"Вы поставили рейтинг: {rating}⭐️",
        reply_markup=None  # This removes the inline keyboard
    )

                
async def download_video(message: types.Message):
    video = message.video
    file_info = await bot.get_file(video.file_id)
    file_path = file_info.file_path
    new_file_name = f"demo_{message.message_id}.mp4"  
    await bot.download_file(file_path, new_file_name)
    await message.reply("Видео сохранено, начинаю обработку...")
    await queue.put((message, new_file_name))  

async def download_round_video(message: types.Message):
    video_note = message.video_note
    file_info = await bot.get_file(video_note.file_id)
    file_path = file_info.file_path
    new_file_name = f"demo_{message.message_id}.mp4"  
    await bot.download_file(file_path, new_file_name)
    await message.reply("Видео сохранено, начинаю обработку...")
    await queue.put((message, new_file_name))  

from aiogram.contrib.middlewares.logging import LoggingMiddleware
dp.register_message_handler(download_video, content_types=types.ContentType.VIDEO)
dp.register_message_handler(download_round_video, content_types=types.ContentType.VIDEO_NOTE)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    queue = asyncio.Queue()  # исправлено для определения в правильном контексте
    
    for _ in range(2):  # создаем два обработчика
        loop.create_task(video_worker())
    
    # Your existing asyncio queue and task creation from above goes here...
    dp.middleware.setup(LoggingMiddleware())
    # Instead of executor.start_polling(dp, skip_updates=True), use this:
    executor.start_polling(dp, loop=loop, skip_updates=True)

    loop.close()