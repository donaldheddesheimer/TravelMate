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
from packing.models import PackingList, PackingItem
import json
from django.conf import settings
from datetime import datetime, timedelta
import logging
from functools import partial
from django.core.cache import cache
from django.http import JsonResponse

logger = logging.getLogger(__name__)

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


@cache_page(60 * 60)  # Cache for 1 hour
def generate_packing_list(request, trip_id):
    logger.info(f"Received packing list generation request for trip_id: {trip_id}")
    try:
        trip = Trip.objects.get(id=trip_id)
        logger.info(f"Found trip: {trip.destination} (ID: {trip_id})")
        
        # Check if we should regenerate
        regenerate = request.GET.get('regenerate', 'false').lower() == 'true'
        logger.info(f"Regenerate flag: {regenerate}")
        
        if regenerate:
            # Clear existing cache
            cache.delete(f'packing_list_{trip_id}')
            logger.info("Cleared existing cache")
            # Delete existing non-custom items
            deleted_count = PackingItem.objects.filter(packing_list__trip=trip, custom_added=False).delete()[0]
            logger.info(f"Deleted {deleted_count} existing non-custom items")
        
        # Get or create packing list
        packing_list, created = PackingList.objects.get_or_create(trip=trip)
        logger.info(f"{'Created new' if created else 'Found existing'} packing list for trip")
        
        # Generate new packing list using AI
        logger.info("Calling PackingListGenerator to generate new list")
        response = PackingListGenerator.generate_packing_list(trip)
        
        if not response:
            logger.error("Failed to get response from PackingListGenerator")
            return JsonResponse({'error': 'Failed to generate packing list'}, status=500)
            
        try:
            logger.info("Attempting to parse AI response")
            data = json.loads(response)
            if not isinstance(data, dict) or 'categories' not in data:
                logger.error(f"Invalid response format: {data}")
                return JsonResponse({'error': 'Invalid response format from AI service'}, status=500)
                
            # Create packing items from the response
            logger.info("Creating packing items from response")
            total_items = 0
            for category in data['categories']:
                category_name = category.get('name', 'Uncategorized')
                logger.info(f"Processing category: {category_name}")
                items_in_category = 0
                for item in category.get('items', []):
                    PackingItem.objects.create(
                        packing_list=packing_list,
                        name=item.get('name', ''),
                        category=category_name,
                        quantity=item.get('quantity', 1),
                        is_essential=item.get('essential', False),
                        notes=item.get('notes', ''),
                        for_day=item.get('for_day'),
                        custom_added=False
                    )
                    items_in_category += 1
                    total_items += 1
                    logger.info(f"Created item: {item.get('name', '')}")
                logger.info(f"Created {items_in_category} items in category {category_name}")
                    
            logger.info(f"Successfully generated packing list with {total_items} total items")
            return JsonResponse({
                'success': True,
                'message': 'Packing list generated successfully',
                'items_created': total_items
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Raw response: {response}")
            return JsonResponse({'error': 'Invalid JSON response from AI service'}, status=500)
            
    except Trip.DoesNotExist:
        logger.error(f"Trip not found with ID: {trip_id}")
        return JsonResponse({'error': 'Trip not found'}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error in generate_packing_list: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


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
