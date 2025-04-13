from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from .services import weather
from .services.places import GooglePlacesService
from .services.ai import DeepSeekService
from django.views.decorators.cache import cache_page

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
    location = request.GET.get('location')
    data = GooglePlacesService.search_places(query, location)
    return Response(data)

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
