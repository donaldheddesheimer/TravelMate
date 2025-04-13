import requests
from django.conf import settings

class DeepSeekService:
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL = "deepseek/deepseek-chat-v3-0324:free"

    @classmethod
    def chat_completion(cls, messages, temperature=0.7):
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": cls.MODEL,
            "messages": messages,
            "temperature": temperature
        }

        response = requests.post(
            f"{cls.BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()