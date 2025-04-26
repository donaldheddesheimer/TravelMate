# views.py

import requests
import logging  # Import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET
# Make sure both datetime and timedelta are imported
from datetime import datetime, timedelta, timezone

from trips.models import Trip

# Set up basic logging
logger = logging.getLogger(__name__)


# Create your views here.
@login_required
def forecast_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    # Pass the date format required by the API to the template
    # This helps keep frontend and backend consistent (Optional but good practice)
    api_date_format = '%Y-%m-%d'
    return render(request, 'weather/forecast.html', {
        'trip': trip,
        'active_tab': 'weather',
        'api_date_format': api_date_format  # Pass the format string if needed in JS
    })


@require_GET
def get_weather_view(request):
    city = request.GET.get('city')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not city or not start_date_str or not end_date_str:
        logger.warning("Missing required parameters: city, start_date, or end_date")
        return JsonResponse({"error": "city, start_date and end_date parameters are required"}, status=400)

    # Step 1: Geocode city
    try:
        geo_url = f"https://api.radar.io/v1/geocode/forward?query={city}&limit=1"
        headers = {"Authorization": settings.GEOCODE_API_KEY}
        response = requests.get(geo_url, headers=headers, timeout=10)  # Add timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        geocode_results = response.json()
        if not geocode_results.get("addresses"):
            logger.warning(f"No addresses found for city: {city}")
            return JsonResponse({"error": f"No addresses found for '{city}'"}, status=404)  # Use 404

        address = geocode_results['addresses'][0]
        # Check if coordinates exist
        if 'geometry' not in address or 'coordinates' not in address['geometry'] or len(
                address['geometry']['coordinates']) < 2:
            logger.error(f"Coordinates missing in geocode response for {city}: {address}")
            return JsonResponse({"error": "Could not extract coordinates from geocode result"}, status=500)

        latitude = address['geometry']['coordinates'][1]
        longitude = address['geometry']['coordinates'][0]

    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding request failed for {city}: {e}")
        return JsonResponse({"error": "failed to geocode address"}, status=502)  # 502 Bad Gateway is often appropriate
    except Exception as e:
        logger.error(f"Unexpected error during geocoding for {city}: {e}")
        return JsonResponse({"error": "An unexpected error occurred during geocoding"}, status=500)

    # Step 2: Get forecast data
    try:
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={latitude}&lon={longitude}"
            f"&units=metric&appid={settings.OWM_API_KEY}"
        )
        forecast_response = requests.get(forecast_url, timeout=10)  # Add timeout
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        # Basic check if OWM response looks valid
        if 'list' not in forecast_data or 'city' not in forecast_data:
            logger.error(
                f"Invalid forecast data structure received from OWM for {latitude},{longitude}: {forecast_data}")
            return JsonResponse({"error": "Received invalid data structure from weather service"}, status=502)

    except requests.exceptions.RequestException as e:
        logger.error(f"OWM forecast request failed for {latitude},{longitude}: {e}")
        return JsonResponse({"error": "could not fetch forecast"}, status=502)
    except Exception as e:
        logger.error(f"Unexpected error during forecast fetch for {latitude},{longitude}: {e}")
        return JsonResponse({"error": "An unexpected error occurred fetching forecast"}, status=500)

    # Step 3: Filter forecast to only include trip dates
    try:
        # Parse the date strings into naive datetime objects
        start_dt_naive = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_dt_naive = datetime.strptime(end_date_str, "%Y-%m-%d")

        # --- Important Fix: Adjust the end date for comparison ---
        # Create an exclusive end datetime (start of the day *after* the end date)
        # We assume the input dates represent the start of the day in UTC for filtering.
        end_dt_exclusive = end_dt_naive + timedelta(days=1)

        # Make the start/end datetimes timezone-aware (UTC) for robust comparison
        # (Even though utcfromtimestamp below gives naive, comparing naive UTC is consistent)
        # Or, you could make the item_dt aware too, but comparing naive UTC is simpler here.
        start_dt_utc = start_dt_naive.replace(tzinfo=timezone.utc)
        end_dt_exclusive_utc = end_dt_exclusive.replace(tzinfo=timezone.utc)

        # Check if the requested start date is too far in the future for the OWM API
        now_utc = datetime.now(timezone.utc)
        # OWM free tier is 5 days ahead
        max_forecast_date_utc = now_utc + timedelta(days=5)

        if start_dt_utc > max_forecast_date_utc:
            logger.warning(f"Requested start date {start_date_str} is beyond the 5-day forecast limit.")
            # Return empty list but success status, as the request itself is valid
            return JsonResponse({
                'city': forecast_data['city'],
                'list': [],  # Empty list because it's outside the forecast range
                'trip_duration': (end_dt_naive - start_dt_naive).days + 1,
                'message': 'Requested dates are beyond the available 5-day forecast range.'
            })

        filtered_forecast = []
        for item in forecast_data.get('list', []):  # Use .get for safety
            # --- Important Fix: Use utcfromtimestamp ---
            # Convert OWM's UTC timestamp ('dt') to a naive datetime representing UTC time
            item_dt_naive_utc = datetime.utcfromtimestamp(item['dt'])

            # Now compare the naive UTC datetimes
            if start_dt_naive <= item_dt_naive_utc < end_dt_exclusive:
                filtered_forecast.append(item)

        # Log if filtering resulted in an empty list when OWM provided data
        if forecast_data.get('list') and not filtered_forecast:
            logger.info(
                f"Filtering removed all items. Start: {start_date_str}, End: {end_date_str}. OWM list count: {len(forecast_data.get('list', []))}")
            # You could inspect the first few item['dt'] values from forecast_data here if debugging

        # Return filtered data
        return JsonResponse({
            'city': forecast_data.get('city', {'name': city}),  # Fallback city info
            'list': filtered_forecast,
            'trip_duration': (end_dt_naive - start_dt_naive).days + 1
        })

    except ValueError as e:
        logger.error(f"Date parsing error: {e}. Received start: '{start_date_str}', end: '{end_date_str}'")
        return JsonResponse({"error": f"Invalid date format. Please use YYYY-MM-DD. Error: {e}"}, status=400)
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred during forecast filtering: {e}")  # Use logger.exception to include traceback
        return JsonResponse({"error": "An internal server error occurred during data processing"}, status=500)