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
            logger.info(f"Sending request to AI service with messages: {messages}")
            response = requests.post(
                url=cls.BASE_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Received response from AI service: {data}")
            
            if not data.get("choices"):
                logger.error("No choices in AI response")
                raise ValueError("No choices in AI response")
                
            if not data["choices"][0].get("message"):
                logger.error("No message in AI response choice")
                raise ValueError("No message in AI response choice")
                
            content = data["choices"][0]["message"].get("content")
            if not content:
                logger.error("Empty content in AI response")
                raise ValueError("Empty content in AI response")
                
            logger.info(f"Successfully extracted content from AI response: {content[:100]}...")
            return content
            
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            raise ValueError(f"HTTP error from AI service: {http_err}")
            
        except requests.exceptions.Timeout:
            logger.error("Request to AI service timed out")
            raise ValueError("Request to AI service timed out")
            
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
            raise ValueError(f"Request error: {req_err}")
            
        except Exception as err:
            logger.error(f"Unexpected error occurred: {err}")
            raise ValueError(f"Unexpected error: {err}")
