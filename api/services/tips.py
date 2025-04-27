# api/services/tips.py

import json
import codecs
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

        model_name = getattr(settings, 'OPENROUTER_MODEL', "deepseek/deepseek-chat-v3-0324:free")

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

Generate the travel tips now based on the trip details. Ensure the output is ONLY the JSON object. Do not use bracketed placeholders like [Number].
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
                max_tokens=2000, # Adjust as needed
                extra_headers=extra_headers
            )

            content = completion.choices[0].message.content.strip()

            # --- JSON Cleaning/Extraction ---
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Handle potential leading/trailing junk (like the ']' seen in the warning)
            json_start = content.find('{')
            json_end = content.rfind('}')
            if json_start != -1 and json_end != -1 and json_start < json_end:
                content = content[json_start:json_end + 1]
                logger.info(f"Extracted potential JSON block for trip {trip.id} (tips)")
            else:
                # If we can't even find a { } block, it's definitely not JSON
                logger.error(
                    f"Could not extract valid JSON block from OpenRouter response for trip {trip.id} (tips). Content: {content[:200]}")
                return json.dumps({"error": "AI response did not contain a recognizable JSON structure."})

            # --- Attempt to parse the JSON *here* to validate ---
            try:
                # First, try direct parsing
                parsed_data = json.loads(content)
                logger.info(f"Successfully parsed direct JSON response from OpenRouter for trip {trip.id}")
                # If successful, return the original *valid* JSON string
                return content
            except json.JSONDecodeError as e1:
                logger.warning(
                    f"Direct JSON parsing failed for trip {trip.id}: {e1}. Trying unicode_escape decoding...")
                # If direct parsing fails, *try* unescaping (handles the \")
                try:
                    unescaped_content = codecs.decode(content, 'unicode_escape')
                    # Validate that the unescaped version IS valid JSON
                    parsed_data = json.loads(unescaped_content)
                    logger.info(f"Successfully parsed unicode_escaped JSON response from OpenRouter for trip {trip.id}")
                    # If successful, return the *unescaped* valid JSON string
                    return unescaped_content
                except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e2:
                    logger.error(f"Failed to parse JSON even after unicode_escape for trip {trip.id}: {e2}",
                                 exc_info=True)
                    logger.error(f"Original content: {content[:500]}")
                    logger.error(
                        f"Unescaped content attempt: {unescaped_content[:500] if 'unescaped_content' in locals() else 'N/A'}")
                    return json.dumps(
                        {"error": "AI response was received but could not be parsed as valid JSON after attempts."})

        except OpenAIError as e:
            logger.error(f"OpenRouter API error ({model_name}) during tips generation for trip {trip.id}: {e}", exc_info=True)
            error_message = str(e)
            if hasattr(e, 'body') and isinstance(e.body, dict) and 'message' in e.body:
                 error_message = e.body['message']
            return json.dumps({"error": f"Failed to communicate with AI service: {error_message}"})
        except Exception as e:
            logger.error(f"An unexpected error occurred during OpenRouter call ({model_name}) for tips for trip {trip.id}: {e}", exc_info=True)
            return json.dumps({"error": "An unexpected error occurred during AI generation."})