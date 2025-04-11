import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

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
    print(geocode_results["addresses"][0]['geometry']['coordinates'][1])
    country = geocode_results['addresses'][0]['country']
    city = geocode_results["addresses"][0].get('formattedAddress')
    latitude =geocode_results["addresses"][0]['geometry']['coordinates'][1]
    longitude = geocode_results["addresses"][0]['geometry']['coordinates'][0]

    weather_url = (
        f"https://api.openweathermap.org/data/3.0/onecall?"
        f"lat={latitude}&lon={longitude}&"
        f"exclude=minutely,hourly&"
        f"units=metric&"
        f"appid={settings.OWM_API_KEY}"
    )
    weather_response = requests.get(weather_url)
    if weather_response.status_code != 200:
        return JsonResponse({"error": "could not fetch weather details."}, status=weather_response.status_code)
    weather_forecast = weather_response.json()
    result = {
        "country": country,
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "weather_forecast": weather_forecast
    }
    return JsonResponse(result)


# http://localhost:8000/weather/api/weather/?city=china