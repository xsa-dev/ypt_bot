from aiogram.types import BotCommand
from dotenv import load_dotenv
import os

load_dotenv('.env')

commands = [
    BotCommand("/about_me", "обо мне (селфи, увлечение, история любви и тд)"),
    BotCommand("/granny_faq", "вопросы и ответы бабушке гика"),
    BotCommand("/code", "ссылка на публичный репозиторий"),
    BotCommand("/feature", "дополнительная фича как задание со звездочкой"),
    BotCommand("/start", "начать общение заново")
]

MY_PHOTOS_1 = {
    "name": "СЕЛФИ СОЧИ",
    "image": os.getenv("image_1")
}

MY_PHOTOS_2 = {
    "name": "СЕЛФИ АРМЕНИЯ",
    "image": os.getenv("image_2")
}

MY_VOICE_1 = {
    "name": "GPT",
    "voice": os.getenv("voice_1"),
    "caption": "О GPT для 👵"
}

MY_VOICE_2 = {
    "name": "SQL or NOSQL",
    "voice": os.getenv("voice_2"),
    "caption": "О SQL и NOSQL для 👵"
}

CommandNotRecognized = "Команда не распознана."
AboutMe = """Мое имя Алексей Савин. Мне 35 лет. Я из Москвы и живу в Москве всю свою жизнь. 
Мой сайт: https://alekseysavin.com\r\n
А еще у меня есть микроблог: https://t.me/xsa_logs\r\n
Очень интересно сделать свой курс на тему больших языковых моделей.\r\n
Тут короткая <a href="https://telegra.ph/Istoriya-lyubvi-08-31">история о любви</a>\r\n"""