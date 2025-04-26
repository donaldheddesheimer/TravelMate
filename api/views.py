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


@api_view(['GET'])
@cache_page(60 * 15)
@throttle_classes([UserRateThrottle, AnonRateThrottle])
def weather_forecast(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    date = request.GET.get('date')
    data = weather.WeatherService.get_forecast(lat, lon, date)
    return Response(data)


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
