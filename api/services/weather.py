import requests
from django.conf import settings

class WeatherService:
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    @classmethod
    def get_forecast(cls, lat, lon, date):
        params = {
            'lat': lat,
            'lon': lon,
            'date': date,
            'appid': settings.OWM_API_KEY,
            'units': 'metric'
        }
        response = requests.get(f"{cls.BASE_URL}/forecast", params=params)
        response.raise_for_status()
        return response.json()