from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from .services import weather
from .services.places import GooglePlacesService
from .services.ai import DeepSeekService
from django.views.decorators.cache import cache_page
from api.services.packing import PackingListGenerator
from trips.models import Trip
import json
from django.conf import settings
from datetime import datetime, timedelta
import logging
from functools import partial


# @api_view(['GET'])
# @cache_page(60 * 15)
# @throttle_classes([UserRateThrottle, AnonRateThrottle])
# def weather_forecast(request):
#     lat = request.GET.get('lat')
#     lon = request.GET.get('lon')
#     date = request.GET.get('date')
#     data = weather.WeatherService.get_forecast(lat, lon, date)
#     return Response(data)


@api_view(['GET'])
@cache_page(60 * 15)
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def place_search(request):
    query = request.GET.get('q')
    if not query:
        return Response({'results': []})

    try:
        # Get user's approximate location if available
        location = None
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            if profile.location_lat and profile.location_lng:
                location = f"{profile.location_lat},{profile.location_lng}"

        # Get places from Google
        data = GooglePlacesService.search_places(query, location)

        # Format results consistently
        results = []
        for place in data.get('places', [])[:8]:  # Use new API format
            results.append({
                'name': place.get('displayName', {}).get('text', ''),
                'formatted_address': place.get('formattedAddress', ''),
                'location': place.get('location', {})
            })

        return Response({'results': results})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@cache_page(60 * 15)
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def place_autocomplete(request):
    query = request.GET.get('q')
    
    if not query or len(query) < 2:
        return Response({'suggestions': []})

    try:
        if not settings.GOOGLE_API_KEY:
            return Response({'error': 'API key not configured'}, status=500)

        location = None
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            if profile.location_lat and profile.location_lng:
                location = f"{profile.location_lat},{profile.location_lng}"

        data = GooglePlacesService.autocomplete(query, location)
        suggestions = []

        for suggestion in data.get('suggestions', []):
            if 'placePrediction' in suggestion:
                suggestions.append({
                    'type': 'place',
                    'text': suggestion['placePrediction']['text']['text'],
                    'place_id': suggestion['placePrediction']['placeId']
                })
            elif 'queryPrediction' in suggestion:
                suggestions.append({
                    'type': 'query',
                    'text': suggestion['queryPrediction']['text']['text']
                })

        return Response({'suggestions': suggestions})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@cache_page(60 * 60 * 24)  # Cache for 24 hours
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def place_details(request, place_id):
    try:
        data = GooglePlacesService.get_place_details(place_id)
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@cache_page(60 * 15)
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def chatbot(request):
    user_message = request.data.get('message')
    trip_context = request.data.get('trip_context', '')

    messages = [
        {
            "role": "system",
            "content": f"""You are a travel assistant for TravelMate. 
            Current trip details: {trip_context}. 
            Provide concise, helpful answers."""
        },
        {"role": "user", "content": user_message}
    ]

    reply = DeepSeekService.chat_completion(messages)
    return Response({'reply': reply})


@api_view(['POST'])
def generate_packing_list(request, trip_id):
    trip = Trip.objects.get(pk=trip_id)
    try:
        ai_response = PackingListGenerator.generate_packing_list(trip)
        packing_data = json.loads(ai_response)
        return Response(packing_data)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


def get_cache_key(request, *args, **kwargs):
    destination = request.GET.get('destination', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    return f'weather_forecast_{destination}_{start_date}_{end_date}'

@api_view(['GET'])
@cache_page(60 * 60, key_prefix=get_cache_key)
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def weather_forecast(request):
    """
    Get weather forecast using AI service
    """
    logger = logging.getLogger(__name__)
    
    destination = request.GET.get('destination')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    logger.info(f"Received weather forecast request for {destination} from {start_date} to {end_date}")
    logger.info(f"Cache key: weather_forecast_{destination}_{start_date}_{end_date}")

    if not all([destination, start_date, end_date]):
        logger.error("Missing required parameters")
        return Response({'error': 'destination, start_date and end_date parameters are required'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        # Adjust dates by adding one day
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        adjusted_start = start_dt.strftime('%Y-%m-%d')
        adjusted_end = end_dt.strftime('%Y-%m-%d')

        logger.info(f"Generating forecast for {destination} from {adjusted_start} to {adjusted_end}")

        # Prepare prompt for AI service
        prompt = f"""
        Generate a weather forecast for {destination} between {adjusted_start} and {adjusted_end}.
        Return the data in this JSON format:
        {{
            "city": "destination name",
            "forecast": [
                {{
                    "date": "YYYY-MM-DD",
                    "high_temp": number,  # in Fahrenheit
                    "low_temp": number,   # in Fahrenheit
                    "conditions": "description",
                    "icon": "weather-icon-code"  # Use these codes: 01d, 01n, 02d, 02n, 03d, 03n, 04d, 04n, 09d, 09n, 10d, 10n, 11d, 11n, 13d, 13n, 50d, 50n
                }}
            ]
        }}
        Include realistic weather patterns based on the location and time of year.
        Make sure to:
        1. Use Fahrenheit for temperatures
        2. Use the exact dates provided ({adjusted_start} to {adjusted_end})
        3. Use only the specified icon codes
        4. Return at least one forecast entry
        5. Return ONLY the JSON object, no additional text or markdown
        """

        logger.info("Calling AI service for weather forecast")
        try:
            # Call your AI service
            response = DeepSeekService.chat_completion([{
                "role": "system",
                "content": "You are a weather forecasting assistant. Provide accurate weather predictions in the "
                           "requested format. Always use Fahrenheit for temperatures and the specified icon codes. "
                           "Make sure to return at least one forecast entry. Return ONLY the JSON object, no additional text."
            }, {
                "role": "user",
                "content": prompt
            }])

            logger.info(f"Raw AI response: {response}")

            # Parse the response
            try:
                # Try parsing the response directly as JSON first
                try:
                    weather_data = json.loads(response)
                    logger.info("Successfully parsed weather data from direct JSON response")
                except json.JSONDecodeError:
                    # If direct parsing fails, try extracting JSON from markdown
                    try:
                        # Look for JSON in markdown code blocks
                        if '```json' in response:
                            json_str = response.split('```json')[1].split('```')[0].strip()
                        elif '```' in response:
                            json_str = response.split('```')[1].split('```')[0].strip()
                        else:
                            # Try to find JSON-like content
                            import re
                            json_match = re.search(r'\{.*\}', response, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(0)
                            else:
                                raise ValueError("No JSON content found in response")
                        
                        logger.info(f"Extracted JSON string: {json_str}")
                        weather_data = json.loads(json_str)
                        logger.info("Successfully parsed weather data from extracted JSON")
                    except Exception as e:
                        logger.error(f"Failed to extract JSON from response: {str(e)}")
                        raise ValueError(f"Failed to extract JSON from response: {str(e)}")
                
                # Validate the response structure
                if not isinstance(weather_data, dict):
                    logger.error(f"Response is not a dictionary: {type(weather_data)}")
                    raise ValueError("Response is not a dictionary")
                
                if 'forecast' not in weather_data:
                    logger.error("Missing 'forecast' key in response")
                    raise ValueError("Missing 'forecast' key in response")
                
                if not isinstance(weather_data['forecast'], list):
                    logger.error(f"'forecast' is not a list: {type(weather_data['forecast'])}")
                    raise ValueError("'forecast' is not a list")
                
                if len(weather_data['forecast']) == 0:
                    logger.error("No forecast entries returned")
                    raise ValueError("No forecast entries returned")
                
                # Validate each forecast entry
                for i, forecast in enumerate(weather_data['forecast']):
                    required_fields = ['date', 'high_temp', 'low_temp', 'conditions', 'icon']
                    missing_fields = [field for field in required_fields if field not in forecast]
                    if missing_fields:
                        logger.error(f"Forecast entry {i} missing fields: {missing_fields}")
                        raise ValueError(f"Forecast entry {i} missing required fields: {missing_fields}")
                
                logger.info(f"Successfully generated forecast with {len(weather_data['forecast'])} days")
                return Response(weather_data)

            except Exception as e:
                logger.error(f"Error parsing AI response: {str(e)}")
                logger.error(f"Raw response: {response}")
                return Response({'error': f'Failed to parse AI response: {str(e)}'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            logger.error(f"AI service error: {str(e)}")
            return Response({'error': f'AI service error: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error generating weather forecast: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
