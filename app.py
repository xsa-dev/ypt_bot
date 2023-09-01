import asyncio
import os
import queue
import threading

from aiogram import Bot, Dispatcher, types
from aiogram import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from dotenv import load_dotenv
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import commands, MY_PHOTOS_1, MY_PHOTOS_2, CommandNotRecognized, MY_VOICE_1, MY_VOICE_2, AboutMe
from feature_x import return_one_gif, get_answer_from_gpt_model, send_commands_vector_sync

load_dotenv('.env')
TG_TOKEN = os.getenv("TG_TOKEN")
REPO_URL = os.getenv("REPO_URL")

bot = Bot(token=TG_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
commands_vector = []
result_queue = queue.Queue()


async def send_message_async(chat_id, text):
    await bot.send_message(chat_id, text)


async def check_queue_and_send_messages():
    global result_queue
    if not result_queue.empty():
        message, message_text, file = result_queue.get()
        await send_message_async(message.from_user.id, message_text)
        os.remove(file)



async def set_commands():
    await bot.set_my_commands(commands)


@dp.message_handler(content_types='voice')
async def recognize_command(message: types.Message):
    global dp
    global result_queue
    await bot.send_chat_action(message.from_user.id, "typing")
    try:
        tg_file = await bot.get_file(message.voice.file_id)
        await bot.download_file(tg_file.file_path, destination=tg_file.file_path)
        my_thread = threading.Thread(
            target=lambda: result_queue.put(send_commands_vector_sync(bot, message, tg_file.file_path)))
        my_thread.start()

    except Exception as E:
        command = CommandNotRecognized
        await message.reply(command)


@dp.message_handler(Command("start"))
async def start(message: types.Message, state: FSMContext):
    f_text = ""
    for command in commands:
        f_text += f"{command.command} - {command.description}\r\n"

    await message.reply(
        "привет! Я бот для тестового задания яндекс.практикум.\n\nдоступные команды:\n" + \
        f_text,
        reply_markup=types.ReplyKeyboardMarkup(keyboard=None)
    )


@dp.callback_query_handler(lambda callback: callback.data == MY_VOICE_1['name'] or callback.data == MY_VOICE_2['name'])
async def send_voice(callback: types.CallbackQuery, state: FSMContext):
    await bot.send_chat_action(callback.from_user.id, "upload_voice")

    if callback.data == MY_VOICE_1['name']:
        await bot.send_audio(
            chat_id=callback.from_user.id, audio=MY_VOICE_1['voice'], caption=MY_VOICE_1['caption']
        )
        await callback.answer()
    elif callback.data == MY_VOICE_2['name']:
        await bot.send_voice(
            chat_id=callback.from_user.id, voice=MY_VOICE_2['voice'], caption=MY_VOICE_2['caption']
        )
        await callback.answer()
    else:
        await callback.message.reply(CommandNotRecognized)
        await callback.answer()


@dp.message_handler(lambda message: message.text == MY_PHOTOS_1['name'] or message.text == MY_PHOTOS_2['name'])
async def send_photo(message: types.Message, state: FSMContext):
    if message.text == MY_PHOTOS_1['name']:
        await bot.send_photo(
            chat_id=message.from_user.id,
            photo=MY_PHOTOS_1.get('image' or None),
            caption=MY_PHOTOS_1.get('caption' or None)
        )
    elif message.text == MY_PHOTOS_2['name']:
        await bot.send_photo(
            chat_id=message.from_user.id,
            photo=MY_PHOTOS_2.get('image' or None),
            caption=MY_PHOTOS_2.get('caption' or None)
        )
    else:
        await message.reply(CommandNotRecognized)


@dp.message_handler(Command("about_me"))
async def about_me(message: types.Message, state: FSMContext):
    # Посмотреть 1. твое последнее селфи и 2. фото из старшей школы
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton(MY_PHOTOS_1['name'])
    button2 = types.KeyboardButton(MY_PHOTOS_2['name'])
    button3 = types.KeyboardButton("/start")
    button4 = types.KeyboardButton("/feature")
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    answer_text = ('<b>about_me</b>\r\n' + f"{AboutMe}"
                   + "\r\n<i>чтобы посмотреть больше обо мне, выбери на клавиатуре что именно хотел бы увидеть.</i>")
    await bot.send_message(chat_id=message.from_user.id,
                           text=answer_text,
                           reply_markup=keyboard,
                           parse_mode='html',
                           disable_web_page_preview=True)


@dp.message_handler(Command("granny_faq"))
async def granny_faq(message: types.Message, state: FSMContext):
    # отправить войсы на тему бабушкиных вопросов
    inline_keyboard = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(MY_VOICE_1.get('name' or None), callback_data=MY_VOICE_1.get('name' or None))
    button2 = types.InlineKeyboardButton(MY_VOICE_2.get('name' or None), callback_data=MY_VOICE_2.get('name' or None))

    inline_keyboard.add(button1, button2)
    await message.reply(
        '<b>granny_faq</b>\r\nо сложном для бабушки',
        reply_markup=inline_keyboard,
        parse_mode='html'
    )
    return


@dp.message_handler(Command("code"))
async def code(message: types.Message, state: FSMContext):
    await message.reply(REPO_URL)


@dp.message_handler(Command("feature"))
async def feature(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.from_user.id, action='typing')
    task1 = asyncio.create_task(get_answer_from_gpt_model())
    task2 = asyncio.create_task(return_one_gif())
    await asyncio.gather(task1, task2)
    caption = task1.result()
    random_gif = task2.result()

    video_file = random_gif['images']['original']['mp4']
    await bot.send_video(
        chat_id=message.from_user.id, video=video_file, caption=caption
    )


if __name__ == "__main__":
    # queue processing
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_queue_and_send_messages, 'interval', seconds=10)
    scheduler.start()

    # set commands
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(set_commands(), loop=loop)

    # bot polling
    executor.start_polling(dp, skip_updates=False)
