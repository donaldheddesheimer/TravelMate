# api/services/tips.py

import json
import logging
from django.conf import settings
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

class TravelTipsGenerator:
    @staticmethod
    def generate_travel_tips(trip): # No weather_summary needed here unless desired later
        """
        Generates travel tips using an OpenAI compatible API (like OpenRouter)
        based on trip details.

        Args:
            trip: The Trip object.

        Returns:
            str: The raw JSON string response from the AI or a JSON string containing an error.
        """
        if not hasattr(settings, 'OPENROUTER_API_KEY') or not settings.OPENROUTER_API_KEY:
             logger.error("OPENROUTER_API_KEY not configured in Django settings.")
             return json.dumps({"error": "AI service API key not configured."})

        try:
            client = OpenAI(
              base_url="https://openrouter.ai/api/v1",
              api_key=settings.OPENROUTER_API_KEY,
            )
            site_url = getattr(settings, 'YOUR_SITE_URL_SETTING', None)
            site_name = getattr(settings, 'YOUR_SITE_NAME_SETTING', None)
            extra_headers = {}
            if site_url:
                extra_headers["HTTP-Referer"] = site_url
            if site_name:
                extra_headers["X-Title"] = site_name
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client for OpenRouter: {e}", exc_info=True)
            return json.dumps({"error": f"Failed to initialize AI client: {e}"})

        model_name = "deepseek/deepseek-chat-v3-0324:free"

        # --- Updated Prompt for Travel Tips ---
        prompt = f"""Create a list of helpful travel tips in JSON format for a trip to {trip.destination} from {trip.date_leaving.strftime('%Y-%m-%d')} to {trip.date_returning.strftime('%Y-%m-%d')}.

Consider the following details:
Destination: {trip.destination}
Dates: {trip.date_leaving.strftime('%b %d, %Y')} to {trip.date_returning.strftime('%b %d, %Y')}
Planned Activities: {trip.activities or 'General tourism and leisure'}

The output MUST be a valid JSON object containing a single key "categories".
The "categories" key should hold a list of category objects.
Each category object should have a "name" (string) and an "items" (list) key.
The "name" should be one of: "Cultural Advice", "Local Information", "Must Have Items".
Each item object in the "items" list should have a single key:
- "tip" (string, required): The text of the travel tip.

Example JSON structure:
{{
    "categories": [
        {{
            "name": "Cultural Advice",
            "items": [
                {{"tip": "Learn a few basic local phrases like 'hello' and 'thank you'."}},
                {{"tip": "Dress modestly when visiting religious sites."}}
            ]
        }},
        {{
            "name": "Local Information",
            "items": [
                {{"tip": "The local currency is [Currency Name]. Credit cards are widely accepted, but carry some cash."}},
                {{"tip": "Public transport is efficient. Consider buying a multi-day pass."}},
                {{"tip": "Emergency number is [Number]." }}
            ]
        }},
        {{
            "name": "Must Have Items",
            "items": [
                {{"tip": "Comfortable walking shoes are essential."}},
                {{"tip": "A universal travel adapter if coming from abroad."}},
                {{"tip": "Sunscreen and a hat, especially during summer months."}}
            ]
        }}
        // Add other relevant tips based on destination/activities.
    ]
}}

Generate the travel tips now based on the trip details. Ensure the output is ONLY the JSON object.
"""

        try:
            logger.info(f"Sending travel tips request to OpenRouter ({model_name}) for trip {trip.id} to {trip.destination}")

            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful travel assistant. Your task is to generate travel tips in JSON format based on the user's trip details and activities. Output ONLY the JSON object with categories: 'Cultural Advice', 'Local Information', 'Must Have Items'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7, # Slightly higher temperature for potentially more varied tips
                max_tokens=1000, # Adjust as needed
                extra_headers=extra_headers
            )

            content = completion.choices[0].message.content.strip()

            # --- JSON Cleaning/Extraction (same logic as before) ---
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            if not (content.startswith('{') and content.endswith('}')):
                 logger.warning(f"OpenRouter ({model_name}) response for trip {trip.id} (tips) doesn't look like JSON: {content[:100]}...")
                 json_start = content.find('{')
                 json_end = content.rfind('}')
                 if json_start != -1 and json_end != -1 and json_start < json_end:
                     content = content[json_start:json_end+1]
                     logger.info(f"Extracted potential JSON from OpenRouter response for trip {trip.id} (tips)")
                 else:
                     logger.error(f"Could not extract valid JSON from OpenRouter response for trip {trip.id} (tips)")
                     return json.dumps({"error": "AI response was not in the expected JSON format."})
            # --------------------------------------------------------

            logger.info(f"Received travel tips response from OpenRouter for trip {trip.id}")
            return content

        except OpenAIError as e:
            logger.error(f"OpenRouter API error ({model_name}) during tips generation for trip {trip.id}: {e}", exc_info=True)
            error_message = str(e)
            if hasattr(e, 'body') and isinstance(e.body, dict) and 'message' in e.body:
                 error_message = e.body['message']
            return json.dumps({"error": f"Failed to communicate with AI service: {error_message}"})
        except Exception as e:
            logger.error(f"An unexpected error occurred during OpenRouter call ({model_name}) for tips for trip {trip.id}: {e}", exc_info=True)
            return json.dumps({"error": "An unexpected error occurred during AI generation."})