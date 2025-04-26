import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
from datetime import datetime, timedelta

from trips.models import Trip


# Create your views here.
@login_required
def forecast_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    return render(request, 'weather/forecast.html', {
        'trip': trip,
        'active_tab': 'weather'
    })


@require_GET
def get_weather_view(request):
    city = request.GET.get('city')
    start_date = request.GET.get('start_date')  # New: trip start date
    end_date = request.GET.get('end_date')  # New: trip end date

    if not city or not start_date or not end_date:
        return JsonResponse({"error": "city, start_date and end_date parameters are required"}, status=400)

    # Step 1: Geocode city to get coordinates (same as before)
    geo_url = f"https://api.radar.io/v1/geocode/forward?query={city}&limit=1"
    headers = {"Authorization": settings.GEOCODE_API_KEY}
    response = requests.get(geo_url, headers=headers)

    if response.status_code != 200:
        return JsonResponse({"error": "failed to geocode address"}, status=response.status_code)

    geocode_results = response.json()
    if len(geocode_results.get("addresses", [])) == 0:
        return JsonResponse({"error": "No addresses found"})

    latitude = geocode_results['addresses'][0]['geometry']['coordinates'][1]
    longitude = geocode_results['addresses'][0]['geometry']['coordinates'][0]

    # Step 2: Get forecast data
    forecast_url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={latitude}&lon={longitude}"
        f"&units=metric&appid={settings.OWM_API_KEY}"
    )
    forecast_response = requests.get(forecast_url)

    if forecast_response.status_code != 200:
        return JsonResponse({"error": "could not fetch forecast"}, status=forecast_response.status_code)

    forecast_data = forecast_response.json()

    # Step 3: Filter forecast to only include trip dates
    try:
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        filtered_forecast = [
            item for item in forecast_data['list']
            if start_dt <= datetime.fromtimestamp(item['dt']) <= end_dt
        ]

        # Return filtered data with original city info
        return JsonResponse({
            'city': forecast_data['city'],
            'list': filtered_forecast,
            'trip_duration': (end_dt - start_dt).days + 1  # Include both start and end days
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


        # https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={part}&appid={API key}