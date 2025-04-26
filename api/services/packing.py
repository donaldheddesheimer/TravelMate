# api/services/packing.py (was packing.py)

import openai
import json
import logging
from django.conf import settings
from datetime import timedelta

logger = logging.getLogger(__name__)

class PackingListGenerator:
    @staticmethod
    def generate_packing_list(trip, weather_summary): # <-- Add weather_summary parameter
        """
        Generates a packing list using OpenAI based on trip details and weather.

        Args:
            trip: The Trip object.
            weather_summary (str): A concise string describing the weather forecast.

        Returns:
            str: The raw JSON string response from OpenAI or a JSON string containing an error.
        """
        openai.api_key = settings.OPENAI_API_KEY # Ensure API key is set

        # Use the provided weather_summary in the prompt
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
            logger.info(f"Sending packing list request to OpenAI for trip {trip.id} to {trip.destination}")
            # Use the newer chat completions endpoint if possible
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", # Or gpt-4 if available/preferred
                messages=[
                    {"role": "system", "content": "You are a travel assistant. Your task is to generate a packing list in JSON format based on the user's trip details, activities, and weather forecast. Output ONLY the JSON object."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6, # Adjust temperature for creativity vs consistency
                max_tokens=1500 # Adjust as needed based on expected list size
            )

            content = response.choices[0].message.content.strip()
            # Sometimes the model might wrap the JSON in markdown ```json ... ```
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip() # Remove leading/trailing whitespace

            # Basic validation: Check if it looks like JSON
            if not (content.startswith('{') and content.endswith('}')):
                 logger.warning(f"OpenAI response for trip {trip.id} doesn't look like JSON: {content[:100]}...")
                 # Attempt to find JSON within the response (simple heuristic)
                 json_start = content.find('{')
                 json_end = content.rfind('}')
                 if json_start != -1 and json_end != -1 and json_start < json_end:
                     content = content[json_start:json_end+1]
                     logger.info(f"Extracted potential JSON from response for trip {trip.id}")
                 else:
                     # If still not JSON, return an error structure
                     logger.error(f"Could not extract valid JSON from OpenAI response for trip {trip.id}")
                     return json.dumps({"error": "AI response was not in the expected JSON format."})


            logger.info(f"Received packing list response from OpenAI for trip {trip.id}")
            return content

        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API error during packing list generation for trip {trip.id}: {e}", exc_info=True)
            # Return a JSON string with an error message
            return json.dumps({"error": f"Failed to communicate with AI service: {e}"})
        except Exception as e:
            logger.error(f"An unexpected error occurred during OpenAI call for trip {trip.id}: {e}", exc_info=True)
            # Return a JSON string with an error message
            return json.dumps({"error": "An unexpected error occurred during AI generation."})