import requests
import json
from django.conf import settings
from django.core.cache import cache


class GooglePlacesService:
    BASE_URL = "https://places.googleapis.com/v1"
    CACHE_TIMEOUT = 60 * 60 * 24  # Cache for 24 hours

    @classmethod
    def autocomplete(cls, query, location=None, radius=None, include_query_predictions=False):
        """
        Get place autocomplete predictions using Google Places API (v1)

        Args:
            query: Partial search query (e.g., "pizza near")
            location: Optional "lat,lng" string for location bias
            radius: Optional radius in meters for location bias
            include_query_predictions: Whether to include query predictions

        Returns:
            Dictionary containing autocomplete suggestions
        """
        cache_key = f"places_autocomplete:{query}:{location}:{radius}:{include_query_predictions}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': settings.GOOGLE_API_KEY,
            'X-Goog-FieldMask': 'suggestions.placePrediction,suggestions.queryPrediction',
        }

        request_body = {
            'input': query,
            'includeQueryPredictions': include_query_predictions,
        }

        # Add location bias if provided
        if location:
            try:
                lat, lng = map(float, location.split(','))
                request_body['locationBias'] = {
                    'circle': {
                        'center': {'latitude': lat, 'longitude': lng},
                        'radius': radius or 5000  # Default 5km radius
                    }
                }
            except (ValueError, AttributeError):
                pass  # Skip invalid location formats

        try:
            response = requests.post(
                f"{cls.BASE_URL}/places:autocomplete",
                headers=headers,
                data=json.dumps(request_body)
            )
            response.raise_for_status()
            data = response.json()

            # Cache the successful response
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return data

        except requests.exceptions.RequestException as e:
            # Fallback to old autocomplete if new one fails
            return cls._fallback_autocomplete(query, location, radius)

    @classmethod
    def search_places(cls, query, location=None, radius=None):
        """
        Search places using Google Places API (v1)

        Args:
            query: The text query (e.g., "restaurants in Paris")
            location: Optional "lat,lng" string for location bias
            radius: Optional radius in meters for location bias

        Returns:
            Dictionary containing places data
        """
        cache_key = f"places_search:{query}:{location}:{radius}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': settings.GOOGLE_API_KEY,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location',
        }

        request_body = {
            'textQuery': query,
            'languageCode': 'en',
        }

        # Add location bias if provided
        if location:
            try:
                lat, lng = map(float, location.split(','))
                request_body['locationBias'] = {
                    'circle': {
                        'center': {'latitude': lat, 'longitude': lng},
                        'radius': radius or 5000  # Default 5km radius
                    }
                }
            except (ValueError, AttributeError):
                pass  # Skip invalid location formats

        try:
            response = requests.post(
                f"{cls.BASE_URL}/places:searchText",
                headers=headers,
                data=json.dumps(request_body)
            )
            response.raise_for_status()
            data = response.json()

            # Cache the successful response
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return data

        except requests.exceptions.RequestException as e:
            # Fallback to old API if new one fails
            return cls._fallback_search(query, location, radius)

    @classmethod
    def _fallback_autocomplete(cls, query, location=None, radius=None):
        """Fallback to the old Places Autocomplete API if new one fails"""
        old_api_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            'key': settings.GOOGLE_API_KEY,
            'input': query,
            'types': 'establishment,address',
            'language': 'en'
        }

        if location:
            params.update({
                'location': location,
                'radius': radius or 5000
            })

        try:
            response = requests.get(old_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Convert old API format to new API format
            return {
                'suggestions': [{
                    'placePrediction': {
                        'text': {'text': prediction['description']},
                        'placeId': prediction['place_id'],
                        'structuredFormat': {
                            'mainText': prediction['structured_formatting']['main_text'],
                            'secondaryText': prediction['structured_formatting'].get('secondary_text', '')
                        }
                    }
                } for prediction in data.get('predictions', [])]
            }
        except Exception:
            return {'suggestions': []}

    @classmethod
    def _fallback_search(cls, query, location=None, radius=None):
        """Fallback to the old Places API if new one fails"""
        old_api_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'key': settings.GOOGLE_API_KEY,
            'query': query,
            'language': 'en'
        }

        if location:
            params.update({
                'location': location,
                'radius': radius or 5000
            })

        try:
            response = requests.get(old_api_url, params=params)
            response.raise_for_status()
            data = response.json()

            # Convert old API format to new API format
            return {
                'places': [{
                    'displayName': {'text': place.get('name', '')},
                    'formattedAddress': place.get('formatted_address', ''),
                    'location': {
                        'latitude': place['geometry']['location']['lat'],
                        'longitude': place['geometry']['location']['lng']
                    } if 'geometry' in place else None
                } for place in data.get('results', [])]
            }
        except Exception:
            return {'places': []}

    @classmethod
    def get_place_details(cls, place_id):
        """Get detailed information about a place using its place_id"""
        cache_key = f"place_details:{place_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': settings.GOOGLE_API_KEY,
            'X-Goog-FieldMask': 'id,displayName,formattedAddress,location,rating,userRatingCount,'
                                'photos,regularOpeningHours,websiteUri,addressComponents',
        }

        try:
            response = requests.get(
                f"{cls.BASE_URL}/places/{place_id}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            # Cache the successful response
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return data

        except requests.exceptions.RequestException:
            return cls._fallback_place_details(place_id)

    @classmethod
    def _fallback_place_details(cls, place_id):
        """Fallback to old Places Details API if new one fails"""
        old_api_url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'key': settings.GOOGLE_API_KEY,
            'place_id': place_id,
            'fields': 'name,formatted_address,geometry,rating,user_ratings_total,'
                      'photos,opening_hours,website,address_components'
        }

        try:
            response = requests.get(old_api_url, params=params)
            response.raise_for_status()
            data = response.json().get('result', {})

            # Convert old API format to new API format
            return {
                'id': place_id,
                'displayName': {'text': data.get('name', '')},
                'formattedAddress': data.get('formatted_address', ''),
                'location': {
                    'latitude': data['geometry']['location']['lat'],
                    'longitude': data['geometry']['location']['lng']
                } if 'geometry' in data else None,
                'rating': data.get('rating'),
                'userRatingCount': data.get('user_ratings_total'),
                'photos': data.get('photos', []),
                'regularOpeningHours': data.get('opening_hours', {}),
                'websiteUri': data.get('website', ''),
                'addressComponents': data.get('address_components', [])
            }
        except Exception:
            return {}