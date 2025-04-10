import requests
from django.conf import settings

class GooglePlacesService:
    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    @classmethod
    def search_places(cls, query, location=None, radius=5000):
        params = {
            'key': settings.GOOGLE_API_KEY,
            'query': query,
            'language': 'en'
        }
        if location:  # "lat,lng" format
            params.update({
                'location': location,
                'radius': radius
            })

        response = requests.get(f"{cls.BASE_URL}/textsearch/json", params=params)
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_place_details(cls, place_id):
        params = {
            'key': settings.GOOGLE_API_KEY,
            'place_id': place_id,
            'fields': 'name,formatted_address,rating,photos,opening_hours'
        }
        response = requests.get(f"{cls.BASE_URL}/details/json", params=params)
        response.raise_for_status()
        return response.json()