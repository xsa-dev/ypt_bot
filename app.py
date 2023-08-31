import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram import executor
from dotenv import load_dotenv

from config import commands, MY_PHOTOS_1, MY_PHOTOS_2, CommandNotRecognized, MY_VOICE_1, MY_VOICE_2
from feature_x import return_one_gif, get_answer_from_gpt_model, get_text_from_user_voice, get_commands_vector

load_dotenv('.env')
TG_TOKEN = os.getenv("TG_TOKEN")
REPO_URL = os.getenv("REPO_URL")

bot = Bot(token=TG_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
commands_vector = []


async def set_commands():
    await bot.set_my_commands(commands)


@dp.message_handler(content_types='voice')
async def recognize_command(message: types.Message):
    await bot.send_chat_action(message.from_user.id, "typing")
    directory = './voice'
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    try:
        file_id = message.voice.file_id
        tg_file = await bot.get_file(file_id)
        await bot.download_file(tg_file.file_path, destination=tg_file.file_path)
        command = get_text_from_user_voice(tg_file.file_path)
        request = command.result()
        command = request.text
        os.remove(tg_file.file_path)

        commands_vector = await get_commands_vector(commands=commands, command=command)

        if len(commands_vector) == 0:
            command = CommandNotRecognized + "\r\n" + request.text
        else:
            try:
                recognized_commands = list(set(commands_vector))
                command = request.text + '\r\n'
                command += "\r\n".join(recognized_commands)
            except Exception as E:
                command = CommandNotRecognized

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
    keyboard.add(button1, button2)
    keyboard.add(button3)
    answer_text = ('<b>about_me<b>\r\n' + """
                Мое имя Алексей Савин. Мне 35 лет. Я из Москвы и живу в Москве всю свою жизнь. Мой сайт: https://alekseysavin.com
                А еще у меня есть микроблог: https://t.me/xsa_logs
                Очень интересно сделать свой курс на тему больших языковых моделей.\r\n
                Тут короткая <a src="https://telegra.ph/Istoriya-lyubvi-08-31">история о любви</a>\r\n
                """.strip() + "чтобы посмотреть больше обо мне, выбери на клавиатуре что именно хотел бы увидеть.")
    await bot.send_message(chat_id=message.from_user.id,
                           text=answer_text,
                           reply_markup=keyboard,
                           parse_mode='html')


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
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(set_commands(), loop=loop)
    executor.start_polling(dp, skip_updates=False)
