import requests
import logging
from django.conf import settings
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

def _geocode_city(city):
    """Helper to geocode city name to lat/lon."""
    try:
        geo_url = f"https://api.radar.io/v1/geocode/forward?query={city}&limit=1"
        headers = {"Authorization": settings.GEOCODE_API_KEY}
        response = requests.get(geo_url, headers=headers, timeout=10)
        response.raise_for_status()
        geocode_results = response.json()

        if not geocode_results.get("addresses"):
            logger.warning(f"No addresses found for city: {city}")
            return None, None, f"Could not find coordinates for '{city}'."

        address = geocode_results['addresses'][0]
        if 'geometry' not in address or 'coordinates' not in address['geometry'] or len(address['geometry']['coordinates']) < 2:
            logger.error(f"Coordinates missing in geocode response for {city}: {address}")
            return None, None, "Could not extract coordinates from geocode result."

        latitude = address['geometry']['coordinates'][1]
        longitude = address['geometry']['coordinates'][0]
        return latitude, longitude, None # Return lat, lon, error=None

    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding request failed for {city}: {e}")
        return None, None, "Failed to contact geocoding service."
    except Exception as e:
        logger.error(f"Unexpected error during geocoding for {city}: {e}")
        return None, None, "An unexpected error occurred during geocoding."

def _fetch_owm_forecast(latitude, longitude):
    """Helper to fetch forecast data from OWM."""
    try:
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={latitude}&lon={longitude}"
            f"&units=metric&appid={settings.OWM_API_KEY}"
        )
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        if 'list' not in forecast_data or 'city' not in forecast_data:
            logger.error(f"Invalid forecast data structure received from OWM for {latitude},{longitude}: {forecast_data}")
            return None, "Received invalid data structure from weather service."

        return forecast_data, None # Return data, error=None

    except requests.exceptions.RequestException as e:
        logger.error(f"OWM forecast request failed for {latitude},{longitude}: {e}")
        return None, "Could not fetch forecast data."
    except Exception as e:
        logger.error(f"Unexpected error during forecast fetch for {latitude},{longitude}: {e}")
        return None, "An unexpected error occurred fetching forecast."

def _summarize_forecast(filtered_list, city_name):
    """Creates a concise summary string from filtered forecast data."""
    if not filtered_list:
        return f"No specific forecast data available for the selected dates in {city_name} (may be too far out)."

    temps = [item['main']['temp'] for item in filtered_list]
    feels_like_temps = [item['main']['feels_like'] for item in filtered_list]
    conditions = defaultdict(int)
    precip_chance = False

    for item in filtered_list:
        # Use main description, fallback to description if main isn't specific enough sometimes
        main_condition = item['weather'][0]['main']
        conditions[main_condition] += 1
        # Check for rain/snow probability if available (might not be in free tier detailed)
        if 'pop' in item and item['pop'] > 0.3: # Check probability of precipitation > 30%
             precip_chance = True
        elif main_condition in ['Rain', 'Snow', 'Drizzle', 'Thunderstorm']:
             precip_chance = True # Mark if condition itself implies precipitation


    min_temp = min(temps) if temps else 'N/A'
    max_temp = max(temps) if temps else 'N/A'
    avg_temp = statistics.mean(temps) if temps else 'N/A'
    avg_feels_like = statistics.mean(feels_like_temps) if feels_like_temps else 'N/A'

    # Find the most common condition(s)
    if conditions:
        dominant_conditions = sorted(conditions.items(), key=lambda item: item[1], reverse=True)
        # Take top 1 or 2 dominant conditions
        top_conditions_str = ", ".join([cond[0] for cond in dominant_conditions[:2]])
    else:
        top_conditions_str = "Unknown conditions"


    summary = (
        f"Weather forecast for {city_name}: "
        f"Average temperature around {avg_temp:.1f}°C (feels like {avg_feels_like:.1f}°C). "
        f"Highs reaching near {max_temp:.1f}°C, lows around {min_temp:.1f}°C. "
        f"Conditions mainly {top_conditions_str}. "
    )
    if precip_chance:
        summary += "Possibility of precipitation (rain/snow). "
    else:
        summary += "Likely dry. "

    # Add a note about potential inaccuracy
    summary += " (Note: This is a general forecast for the period)."

    return summary


def fetch_and_summarize_weather(destination, start_date, end_date):
    """
    Fetches weather forecast for a destination and date range,
    and returns a concise summary string.
    """
    logger.info(f"Fetching weather summary for {destination} from {start_date} to {end_date}")

    latitude, longitude, error = _geocode_city(destination)
    if error:
        return f"Weather unavailable: {error}" # Return error message directly

    forecast_data, error = _fetch_owm_forecast(latitude, longitude)
    if error:
        return f"Weather unavailable: {error}" # Return error message directly

    # Filter forecast data to trip dates
    try:
        # Convert model dates (assuming they are date objects) to naive datetime objects at start of day
        start_dt_naive = datetime.combine(start_date, datetime.min.time())
        end_dt_naive = datetime.combine(end_date, datetime.min.time())
        # Create an exclusive end datetime (start of the day *after* the end date) for filtering
        end_dt_exclusive = end_dt_naive + timedelta(days=1)

        # Make aware for comparison safety, although comparing naive UTC from OWM is okay too
        start_dt_utc = start_dt_naive.replace(tzinfo=timezone.utc)
        end_dt_exclusive_utc = end_dt_exclusive.replace(tzinfo=timezone.utc)

        filtered_forecast = []
        for item in forecast_data.get('list', []):
            # Convert OWM's UTC timestamp to a timezone-aware datetime object
            item_dt_utc = datetime.fromtimestamp(item['dt'], tz=timezone.utc)

            # Compare aware datetimes
            if start_dt_utc <= item_dt_utc < end_dt_exclusive_utc:
                filtered_forecast.append(item)

        city_name = forecast_data.get('city', {}).get('name', destination) # Get city name from API if possible
        return _summarize_forecast(filtered_forecast, city_name)

    except Exception as e:
        logger.exception(f"Error processing forecast data for {destination}: {e}")
        return "Weather unavailable: Error processing forecast data."