import openai
import json
from django.conf import settings
from datetime import timedelta


class PackingListGenerator:
    @staticmethod
    def generate_packing_list(trip):

        prompt = f"""Create a packing list for a trip to {trip.destination} from {trip.date_leaving} to {trip.date_returning}.
        Activities: {trip.activities or 'Not specified'}
        Weather: {weather_data}

        Return JSON format with categories and items:
        {{
            "categories": [
                {{
                    "name": "Category Name",
                    "items": [
                        {{
                            "name": "Item name",
                            "quantity": 1,
                            "essential": true,
                            "notes": "",
                            "for_day": "YYYY-MM-DD"
                        }}
                    ]
                }}
            ]
        }}"""

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel assistant that creates packing lists."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content