import json
import logging
from datetime import timedelta
from .ai import DeepSeekService

logger = logging.getLogger(__name__)

class PackingListGenerator:
    @staticmethod
    def generate_packing_list(trip):
        logger.info(f"Starting packing list generation for trip to {trip.destination}")
        
        # Get weather data for the trip
        weather_data = ""
        if hasattr(trip, 'weather_data') and trip.weather_data:
            weather_data = f"Average temperature: {trip.weather_data.get('temp', 'unknown')}°F, " \
                          f"Conditions: {trip.weather_data.get('conditions', 'unknown')}"
            logger.info(f"Found weather data: {weather_data}")
        else:
            weather_data = "Weather information not available"
            logger.info("No weather data available for trip")

        prompt = f"""Create a comprehensive packing list for a trip to {trip.destination} from {trip.date_leaving} to {trip.date_returning}.
        Trip Details:
        - Destination: {trip.destination}
        - Duration: {(trip.date_returning - trip.date_leaving).days} days
        - Activities: {trip.activities or 'Not specified'}
        - Weather: {weather_data}

        Consider the following:
        1. Essential items for the destination and activities
        2. Appropriate clothing for the weather
        3. Travel documents and electronics
        4. Toiletries and personal items
        5. Any special items needed for activities

        Return the response in this EXACT JSON format (no variations in key names):
        {{
            "categories": [
                {{
                    "name": "Category Name",
                    "items": [
                        {{
                            "name": "Item name",
                            "quantity": 1,
                            "essential": true,
                            "notes": "Optional notes about the item",
                            "for_day": "YYYY-MM-DD"  // Optional, only if item is for a specific day
                        }}
                    ]
                }}
            ]
        }}

        Important:
        1. Use EXACTLY these key names: "categories", "items", "name", "quantity", "essential", "notes", "for_day"
        2. Do NOT use variations like "category", "item", or "note"
        3. Include all essential travel items
        4. Consider the trip duration and weather
        5. Include items specific to the activities
        6. Return valid JSON format
        7. Include at least 3 categories with multiple items each"""

        try:
            logger.info("Calling DeepSeek AI service")
            response = DeepSeekService.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a travel assistant that creates detailed and practical packing lists. Always return valid JSON with the exact key names specified."},
                    {"role": "user", "content": prompt}
                ]
            )
            logger.info("Received response from AI service")

            # Validate the response is valid JSON
            try:
                data = json.loads(response)
                logger.info("Successfully validated JSON response")
                
                # Normalize the response structure
                if 'category' in data:
                    data['categories'] = data.pop('category')
                if isinstance(data.get('categories'), list):
                    for category in data['categories']:
                        if 'item' in category:
                            category['items'] = category.pop('item')
                        if isinstance(category.get('items'), list):
                            for item in category['items']:
                                if 'note' in item:
                                    item['notes'] = item.pop('note')
                
                # Validate the structure
                if not isinstance(data, dict) or 'categories' not in data:
                    logger.error(f"Invalid response structure: {data}")
                    return None
                    
                for category in data['categories']:
                    if not isinstance(category, dict) or 'name' not in category or 'items' not in category:
                        logger.error(f"Invalid category structure: {category}")
                        return None
                        
                    for item in category['items']:
                        if not isinstance(item, dict) or 'name' not in item:
                            logger.error(f"Invalid item structure: {item}")
                            return None
                
                return json.dumps(data)
            except json.JSONDecodeError:
                logger.warning("Initial JSON validation failed, attempting to clean response")
                # If the response is not valid JSON, try to fix it
                try:
                    # Remove any markdown code block markers
                    response = response.replace('```json', '').replace('```', '').strip()
                    # Validate the fixed response
                    data = json.loads(response)
                    
                    # Normalize the response structure
                    if 'category' in data:
                        data['categories'] = data.pop('category')
                    if isinstance(data.get('categories'), list):
                        for category in data['categories']:
                            if 'item' in category:
                                category['items'] = category.pop('item')
                            if isinstance(category.get('items'), list):
                                for item in category['items']:
                                    if 'note' in item:
                                        item['notes'] = item.pop('note')
                    
                    # Validate the structure
                    if not isinstance(data, dict) or 'categories' not in data:
                        logger.error(f"Invalid response structure after cleaning: {data}")
                        return None
                        
                    for category in data['categories']:
                        if not isinstance(category, dict) or 'name' not in category or 'items' not in category:
                            logger.error(f"Invalid category structure after cleaning: {category}")
                            return None
                            
                        for item in category['items']:
                            if not isinstance(item, dict) or 'name' not in item:
                                logger.error(f"Invalid item structure after cleaning: {item}")
                                return None
                    
                    logger.info("Successfully cleaned and validated JSON response")
                    return json.dumps(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON after cleaning: {str(e)}")
                    logger.error(f"Cleaned response: {response}")
                    return None
                except Exception as e:
                    logger.error(f"Unexpected error while cleaning JSON: {str(e)}")
                    return None

        except Exception as e:
            logger.error(f"Error in PackingListGenerator: {str(e)}", exc_info=True)
            return None