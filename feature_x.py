import os
import random
from urllib import parse

import aiohttp
from dotenv import load_dotenv
import assemblyai as aai

aai.settings.api_key = os.getenv("AI_API_KEY")

load_dotenv('.env')

import spacy
import spacy.cli
try:
    nlp = spacy.load('ru_core_news_md')
except Exception as E:
    spacy.cli.download("ru_core_news_md")
    nlp = spacy.load('ru_core_news_md')


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


def get_text_from_user_voice(voice_file) -> str:
    config = aai.TranscriptionConfig(language_code="ru")
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe_async(voice_file)
    return transcript


async def get_commands_vector(commands, command, spacy=True) -> list[str]:
    commands_vector = []
    if not spacy:
        for default_command in commands:
            for token in command.split():
                if token in default_command.description.split() or token == default_command.command.replace("/", ""):
                    commands_vector.append(default_command.command)
        return commands_vector
    else:
        for default_command in commands:
            for token in command.split():
                in_lemmas = nlp(token)
                this_lemmas_description = nlp(default_command.description)
                this_lemmas_command = nlp(default_command.command)

                in_lemmas = [token.lemma_.lower() for token in in_lemmas.doc]
                this_lemmas_description = [token.lemma_.lower() for token in this_lemmas_description.doc]
                this_lemmas_command = [token.lemma_.lower() for token in this_lemmas_command.doc]

                if len(in_lemmas[0].lower()) > 1:
                    if in_lemmas[0] in this_lemmas_description or in_lemmas in this_lemmas_command:
                        commands_vector.append(f'{default_command.command} - {default_command.description}')
    return list(set(commands_vector))