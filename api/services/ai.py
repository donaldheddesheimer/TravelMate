import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class DeepSeekService:
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "deepseek/deepseek-chat-v3-0324:free"

    @classmethod
    def chat_completion(cls, messages, temperature=0.7):
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "TravelMate Chatbot",
        }

        payload = {
            "model": cls.MODEL,
            "messages": messages,
            "temperature": temperature
        }

        try:
            response = requests.post(
                url=cls.BASE_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise
        except Exception as err:
            logger.error(f"Unexpected error occurred: {err}")
            raise
