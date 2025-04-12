import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

# Create your views here.
@require_GET
def get_weather_view(request):
    query = request.GET.get('city')
    if not query:
        return JsonResponse({"error": "query parameter is required"}, status=400)
    geo_url = f"https://api.radar.io/v1/geocode/forward?query={query}&limit=1"
    headers = {
        "Authorization" : settings.GEOCODE_API_KEY
    }
    response = requests.get(geo_url, headers=headers)
    if response.status_code != 200:
        return JsonResponse({"error": "failed to geocode address"}, status=response.status_code)
    geocode_results = response.json()

    if len(geocode_results.get("addresses", [])) == 0:
        return JsonResponse({"error": "No addresses found"})
    country = geocode_results['addresses'][0]['country']
    city = geocode_results["addresses"][0].get('formattedAddress')
    latitude =geocode_results["addresses"][0]['geometry']['coordinates'][1]
    longitude = geocode_results["addresses"][0]['geometry']['coordinates'][0]

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&units=imperial&appid={settings.OWM_API_KEY}"

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