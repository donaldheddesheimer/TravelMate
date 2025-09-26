# test_apis.py
import os
import requests
from django.conf import settings


def test_geocode_api():
    """Test Geocode API"""
    try:
        headers = {"Authorization": os.getenv('GEOCODE_API_KEY')}
        response = requests.get(
            f"https://api.radar.io/v1/geocode/forward?query=Atlanta&limit=1", headers=headers)
        return response.status_code == 200
    except:
        return False


def test_weather_api():
    """Test OpenWeatherMap API"""
    try:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q=London&appid={os.getenv('OWM_API_KEY')}")
        return response.status_code == 200
    except:
        return False


def test_openrouter_api():
    """Test OpenRouter API"""
    try:
        headers = {'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}'}
        response = requests.get('https://openrouter.ai/api/v1/models', headers=headers)
        return response.status_code in [200, 401]  # 401 means key works but no access
    except:
        return False


def test_google_api():
    """Test Google API"""
    try:
        response = requests.get(
            f"https://maps.googleapis.com/maps/api/geocode/json?address=Atlanta&key={os.getenv('GOOGLE_API_KEY')}")
        return response.status_code == 200
    except:
        return False


# Run tests
if __name__ == "__main__":
    apis = {
        "Geocode": test_geocode_api(),
        "Weather": test_weather_api(),
        "OpenRouter": test_openrouter_api(),
        "Google": test_google_api()
    }

    for api_name, status in apis.items():
        print(f"{api_name}: {'✅ Working' if status else '❌ Failed'}")