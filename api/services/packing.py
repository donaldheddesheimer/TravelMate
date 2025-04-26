# api/services/packing.py

import json
import logging
from django.conf import settings
from openai import OpenAI, OpenAIError # Import OpenAI and its specific error class

logger = logging.getLogger(__name__)

class PackingListGenerator:
    @staticmethod
    def generate_packing_list(trip, weather_summary): # <-- weather_summary parameter remains
        """
        Generates a packing list using an OpenAI compatible API (like OpenRouter)
        based on trip details and weather.

        Args:
            trip: The Trip object.
            weather_summary (str): A concise string describing the weather forecast.

        Returns:
            str: The raw JSON string response from the AI or a JSON string containing an error.
        """
        # Ensure API key is set in settings
        if not hasattr(settings, 'OPENROUTER_API_KEY') or not settings.OPENROUTER_API_KEY:
             logger.error("OPENROUTER_API_KEY not configured in Django settings.")
             return json.dumps({"error": "AI service API key not configured."})

        # --- OpenAI Client Initialization with OpenRouter ---
        try:
            client = OpenAI(
              base_url="https://openrouter.ai/api/v1",
              api_key=settings.OPENROUTER_API_KEY,
            )

            # --- Optional OpenRouter Headers ---
            # Get Site URL and Name from Django settings if they exist
            # Replace 'YOUR_SITE_URL_SETTING' and 'YOUR_SITE_NAME_SETTING'
            # with the actual names of your settings variables.
            site_url = getattr(settings, 'YOUR_SITE_URL_SETTING', None)
            site_name = getattr(settings, 'YOUR_SITE_NAME_SETTING', None)

            extra_headers = {}
            if site_url:
                extra_headers["HTTP-Referer"] = site_url
            if site_name:
                extra_headers["X-Title"] = site_name
            # --------------------------------------

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client for OpenRouter: {e}", exc_info=True)
            return json.dumps({"error": f"Failed to initialize AI client: {e}"})
        # ----------------------------------------------------

        # Define the model to use (consider making this a setting)
        # Using the model from your example, but you might want GPT-3.5/4
        # model_name = "microsoft/mai-ds-r1:free"
        # Or stick with gpt-3.5-turbo if preferred and available on OpenRouter
        model_name = getattr(settings, 'OPENROUTER_CHAT_MODEL', "gpt-3.5-turbo") # Default to gpt-3.5-turbo if not set

        prompt = f"""Create a detailed packing list in JSON format for a trip to {trip.destination} from {trip.date_leaving.strftime('%Y-%m-%d')} to {trip.date_returning.strftime('%Y-%m-%d')}.

Consider the following details:
Destination: {trip.destination}
Dates: {trip.date_leaving.strftime('%b %d, %Y')} to {trip.date_returning.strftime('%b %d, %Y')}
Planned Activities: {trip.activities or 'General tourism and leisure'}
Weather Forecast Summary: {weather_summary}

The output MUST be a valid JSON object containing a single key "categories".
The "categories" key should hold a list of category objects.
Each category object should have a "name" (string) and an "items" (list) key.
Each item object in the "items" list should have:
- "name" (string, required): The name of the item.
- "quantity" (integer, optional, default 1): How many of this item.
- "essential" (boolean, optional, default false): Is this item essential (e.g., passport, medications)? Mark essentials as true.
- "notes" (string, optional): Brief notes (e.g., 'Waterproof', 'For evening wear').
- "for_day" (string, optional): If item is specific to a day, provide date in 'YYYY-MM-DD' format. Only use if truly day-specific.

Example JSON structure:
{{
    "categories": [
        {{
            "name": "Clothing",
            "items": [
                {{"name": "T-shirts", "quantity": 5, "essential": false, "notes": "Breathable fabric"}},
                {{"name": "Jeans", "quantity": 1, "essential": false}},
                {{"name": "Rain Jacket", "quantity": 1, "essential": true, "notes": "Check weather forecast daily"}}
            ]
        }},
        {{
            "name": "Toiletries",
            "items": [
                {{"name": "Toothbrush", "quantity": 1, "essential": true}},
                {{"name": "Travel-size Shampoo", "quantity": 1, "essential": false}}
            ]
        }},
        {{
            "name": "Documents & Money",
            "items": [
                {{"name": "Passport", "quantity": 1, "essential": true}},
                {{"name": "Local Currency", "quantity": 1, "essential": true, "notes": "Some cash recommended"}}
            ]
        }},
        {{
            "name": "Medications",
            "items": [
                {{"name": "Prescription Medication", "quantity": 1, "essential": true, "notes": "Bring prescription copy"}},
                {{"name": "Pain Relievers", "quantity": 1, "essential": false}}
            ]
        }}
        // ... other relevant categories like Electronics, Gear (if activities specified), etc.
    ]
}}

Generate the packing list now based on the trip details and weather. Ensure the output is ONLY the JSON object.
"""

        try:
            logger.info(f"Sending packing list request to OpenRouter ({model_name}) for trip {trip.id} to {trip.destination}")

            # --- Use the new client.chat.completions.create method ---
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a travel assistant. Your task is to generate a packing list in JSON format based on the user's trip details, activities, and weather forecast. Output ONLY the JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6, # Adjust temperature for creativity vs consistency
                max_tokens=1500, # Adjust as needed based on expected list size
                extra_headers=extra_headers # Pass the optional headers
            )
            # ----------------------------------------------------------

            content = completion.choices[0].message.content.strip()

            # --- JSON Cleaning/Extraction (same logic as before) ---
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            if not (content.startswith('{') and content.endswith('}')):
                 logger.warning(f"OpenRouter ({model_name}) response for trip {trip.id} doesn't look like JSON: {content[:100]}...")
                 json_start = content.find('{')
                 json_end = content.rfind('}')
                 if json_start != -1 and json_end != -1 and json_start < json_end:
                     content = content[json_start:json_end+1]
                     logger.info(f"Extracted potential JSON from OpenRouter response for trip {trip.id}")
                 else:
                     logger.error(f"Could not extract valid JSON from OpenRouter response for trip {trip.id}")
                     return json.dumps({"error": "AI response was not in the expected JSON format."})
            # --------------------------------------------------------

            logger.info(f"Received packing list response from OpenRouter for trip {trip.id}")
            return content

        except OpenAIError as e: # Catch specific OpenAI/OpenRouter API errors
            logger.error(f"OpenRouter API error ({model_name}) during packing list generation for trip {trip.id}: {e}", exc_info=True)
            # Try to provide a more specific error message if available
            error_message = str(e)
            if hasattr(e, 'body') and isinstance(e.body, dict) and 'message' in e.body:
                 error_message = e.body['message'] # Extract message from error body if possible
            return json.dumps({"error": f"Failed to communicate with AI service: {error_message}"})
        except Exception as e:
            logger.error(f"An unexpected error occurred during OpenRouter call ({model_name}) for trip {trip.id}: {e}", exc_info=True)
            return json.dumps({"error": "An unexpected error occurred during AI generation."})