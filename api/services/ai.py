# api/services/ai.py

import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class DeepSeekService: # Consider renaming if not using DeepSeek models primarily
    MODEL = getattr(settings, 'OPENROUTER_CHAT_MODEL', "google/gemini-2.5-flash-preview")
    BASE_URL = getattr(settings, 'OPENROUTER_BASE_URL', "https://openrouter.ai/api/v1") + "/chat/completions"
    # Default max_tokens value - can be overridden by settings or method call
    DEFAULT_MAX_TOKENS = getattr(settings, 'OPENROUTER_CHAT_DEFAULT_MAX_TOKENS', 5000) # Added default

    @classmethod
    def chat_completion(cls, messages, temperature=0.7, max_tokens=None): # Added max_tokens parameter
        """
        Sends a chat completion request to the OpenRouter API.

        Args:
            messages (list): A list of message dictionaries (e.g., [{"role": "user", "content": "Hello"}]).
            temperature (float, optional): Controls randomness. Defaults to 0.7.
            max_tokens (int, optional): The maximum number of tokens to generate.
                                         Defaults to cls.DEFAULT_MAX_TOKENS (from settings or 250).

        Returns:
            str: The content of the AI's reply.

        Raises:
            ValueError: If API key is missing or response format is invalid.
            ConnectionError: If there's a network issue communicating with the API.
            TimeoutError: If the request times out.
            Exception: For other API-reported errors or unexpected issues.
        """
        api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        if not api_key:
             logger.error("OPENROUTER_API_KEY not configured in Django settings.")
             raise ValueError("AI service API key not configured.")

        site_url = getattr(settings, 'YOUR_SITE_URL_SETTING', 'http://localhost') # Replace placeholder
        site_name = getattr(settings, 'YOUR_SITE_NAME_SETTING', 'TravelMate Chatbot') # Replace placeholder

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": site_url,
            "X-Title": site_name,
        }

        # Determine the final max_tokens value to use
        # Use the value passed to the function if provided, otherwise use the class default
        final_max_tokens = max_tokens if max_tokens is not None else cls.DEFAULT_MAX_TOKENS

        payload = {
            "model": cls.MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": final_max_tokens  # <-- Added max_tokens here
        }

        try:
            logger.info(f"Sending chat request to OpenRouter ({cls.MODEL}) with max_tokens={final_max_tokens}.")
            logger.debug(f"Payload: {json.dumps(payload)}")

            response = requests.post(
                url=cls.BASE_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Received response from OpenRouter: {json.dumps(data)}")

            # --- Error checking and data extraction (keep the robust checks from previous answer) ---
            if 'error' in data:
                error_details = data.get('error', {})
                error_message = error_details.get('message', 'Unknown API error')
                logger.error(f"OpenRouter API returned an error: {error_message} - Full Response: {data}")
                raise Exception(f"AI service error: {error_message}")

            choices = data.get('choices')
            if not choices or not isinstance(choices, list) or len(choices) == 0:
                logger.error(f"OpenRouter response missing 'choices' list or empty. Response: {data}")
                raise ValueError("AI service returned an unexpected response format (no choices).")

            message = choices[0].get('message')
            if not message or not isinstance(message, dict):
                logger.error(f"OpenRouter response choice missing 'message' dict. Choice: {choices[0]}")
                raise ValueError("AI service returned an unexpected response format (no message).")

            content = message.get('content')
            if content is None:
                 logger.error(f"OpenRouter response message missing 'content'. Message: {message}")
                 raise ValueError("AI service returned an unexpected response format (no content).")
            # ------------------------------------------------------------------------------------

            logger.info(f"Successfully received chat completion from OpenRouter ({cls.MODEL}).")
            return content

        # --- Exception handling (keep the robust handling from previous answer) ---
        except requests.exceptions.Timeout:
            logger.error(f"Request to OpenRouter timed out after {30} seconds.")
            raise TimeoutError("The request to the AI service timed out.")
        except requests.exceptions.HTTPError as http_err:
            error_body = ""
            try:
                if http_err.response is not None:
                    error_body = http_err.response.text
            except Exception:
                error_body = "[Could not retrieve response body]"
            logger.error(f"HTTP error occurred: {http_err} - Response Body: {error_body}")
            raise ConnectionError(f"AI service communication failed (HTTP {http_err.response.status_code}). Check logs for details.")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network error during request to OpenRouter: {req_err}")
            raise ConnectionError(f"Could not connect to AI service: {req_err}")
        except json.JSONDecodeError as json_err:
             logger.error(f"Failed to decode JSON response from OpenRouter: {json_err} - Raw Response: {response.text[:500]}...")
             raise ValueError("AI service returned an invalid response (not JSON).")
        except (KeyError, IndexError, TypeError, ValueError) as data_err:
             logger.error(f"Error processing successful AI response structure: {data_err} - Data: {data}", exc_info=True)
             raise ValueError("AI service returned data in an unexpected format.")
        except Exception as err:
            logger.error(f"Unexpected error occurred during chat completion: {err}", exc_info=True)
            raise
        # --------------------------------------------------------------------------