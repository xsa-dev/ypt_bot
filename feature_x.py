import asyncio
import os
import random
from urllib import parse

import aiohttp
from dotenv import load_dotenv
import assemblyai as aai

from config import CommandNotRecognized

aai.settings.api_key = os.getenv("AI_API_KEY")

load_dotenv('.env')

import spacy
import spacy.cli

try:
    nlp = spacy.load('ru_core_news_md')
except Exception as E:
    spacy.cli.download("ru_core_news_md")
    nlp = spacy.load('ru_core_news_md')

config = aai.TranscriptionConfig(language_code="ru")
transcriber = aai.Transcriber(config=config)


async def return_one_gif(query=os.getenv("GIPHY_QUERY", "funny sandwich"), limit=100, randomize=True):
    url = "https://api.giphy.com/v1/gifs/search"
    params = parse.urlencode({
        "q": query,
        "api_key": os.getenv("GIPHY_API_KEY"),
        "limit": limit
    })
    url = "".join((url, "?", params))
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            items = data['data']
            if randomize:
                return random.choice(items)
            else:
                return items[0]


async def get_answer_from_gpt_model(user_text: str = "funny sandwich") -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('YIAM')}",
        "x-folder-id": "b1gmsqg2bg9ovf4uqsf4"
    }
    context = """
        переведи поисковый запрос в веселом стиле
        """.strip()
    text = f"""
        {user_text}
        """.strip()
    params = \
        {
            "model": "general",
            "generationOptions": {
                "partialResults": False,
                "temperature": 0.9,
                "maxTokens": 50
            },
            "instructionText": context,
            "requestText": text
        }

    url = 'https://llm.api.cloud.yandex.net/llm/v1alpha/instruct'
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=params) as response:
            response = await response.json()
            try:
                return response['result']['alternatives'][0]['text']
            except Exception as E:
                return None


async def get_text_from_user_voice(voice_file) -> str:
    global transcriber
    transcript = transcriber.transcribe_async(voice_file)
    return transcript.result().text


from config import commands


def send_commands_vector_sync(bot, message, file):
    def get_text_from_user_voice_sync(file):
        global transcriber
        transcript = transcriber.transcribe(file)
        return transcript.text

    def get_commands():
        voice_command = get_text_from_user_voice_sync(file)
        commands_vector = []
        for default_command in commands:
            for token in voice_command.split():
                in_lemmas = nlp(token)
                this_lemmas_description = nlp(default_command.description)
                this_lemmas_command = nlp(default_command.command)

                in_lemmas = [token.lemma_.lower() for token in in_lemmas.doc]
                this_lemmas_description = [token.lemma_.lower() for token in this_lemmas_description.doc]
                this_lemmas_command = [token.lemma_.lower() for token in this_lemmas_command.doc]

                if len(in_lemmas[0].lower()) > 1:
                    if in_lemmas[0] in this_lemmas_description or in_lemmas in this_lemmas_command:
                        commands_vector.append(f'{default_command.command} - {default_command.description}')
        if len(commands_vector) == 0:
            command = CommandNotRecognized + "\r\n" + voice_command
        else:
            try:
                recognized_commands = list(set(commands_vector))
                command = voice_command + '\r\n'
                command += "\r\n".join(recognized_commands)
            except Exception as E:
                command = CommandNotRecognized
        return command
    command = get_commands()
    return message, command, file
