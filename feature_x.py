import os
import random
from urllib import parse

import aiohttp
from dotenv import load_dotenv

load_dotenv('.env')


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
