import requests
from trips.models import Trip
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

# Create your views here.
@require_GET
def get_weather_view(request, trip_id):
    trip = Trip.objects.get(pk=trip_id)
    destination = trip.destination.split(',')[0].strip()

    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {
            'q': destination,
            'limit': 1,
            'appid': settings.OWM_API_KEY
        }
        
    geo_response = requests.get(geo_url, params=geo_params)
    if geo_response.status_code != 200:
        return JsonResponse({"error": "Failed to geocode location"}, status=geo_response.status_code)
            
    geo_data = geo_response.json()
    if not geo_data:
        return JsonResponse({"error": "Location not found"}, status=404)
            
    location = geo_data[0]
    lat = location['lat']
    lon = location['lon']
    country = location.get('country', '')
    city = location.get('name', destination)

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=imperial&appid={settings.OWM_API_KEY}"

    weather_response = requests.get(weather_url)

    if weather_response.status_code != 200:
        print(weather_response.status_code)
        return JsonResponse({"error": "could not fetch weather details."}, status=weather_response.status_code)
    weather_forecast = weather_response.json()
    sunrise = weather_forecast["sys"]["sunrise"]
    sunset = weather_forecast["sys"]["sunset"]
    timezone = weather_forecast["timezone"]
    sunrise_local = datetime.fromtimestamp(sunrise) + timedelta(seconds=timezone)
    sunset_local = datetime.fromtimestamp(sunset) + timedelta(seconds=timezone)
    sunrise_str = sunrise_local.strftime('%I:%M %p')
    sunset_str = sunset_local.strftime('%I:%M %p')


    result = {
        "country": country,
        "city": city,
        "weather_condition": weather_forecast["weather"][0]["main"],
        "weather_description": weather_forecast["weather"][0]["description"],
        "weather_icon": weather_forecast["weather"][0]["icon"],
        "temp": weather_forecast["main"]["temp"],
        "humidity":weather_forecast["main"]["humidity"],
        "sunrise": sunrise_str,
        "sunset": sunset_str
    }
    return JsonResponse(result)


# http://localhost:8000/weather/api/weather/?city=china
# https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={part}&appid={API key}