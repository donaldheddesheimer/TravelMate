from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from trips.models import Trip
from unittest.mock import patch
import json

class WeatherTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.trip = Trip.objects.create(
            user=self.user,
            destination='New York',
            date_leaving='2024-01-01',
            date_returning='2024-01-07'
        )

    def test_forecast_view_requires_login(self):
        """Test that forecast view requires login"""
        response = self.client.get(reverse('weather:forecast', args=[self.trip.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_forecast_view_renders_template(self):
        """Test that forecast view renders correct template when logged in"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('weather:forecast', args=[self.trip.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'weather/forecast.html')
        self.assertEqual(response.context['trip'], self.trip)
        self.assertEqual(response.context['active_tab'], 'weather')

    @patch('weather.views.requests.get')
    def test_get_weather_success(self, mock_get):
        """Test successful weather API response"""
        # Mock geocode response
        mock_geocode_response = type('Response', (), {
            'status_code': 200,
            'json': lambda: {
                'addresses': [{
                    'country': 'US',
                    'formattedAddress': 'New York, NY, USA',
                    'geometry': {'coordinates': [40.7128, -74.0060]}
                }]
            }
        })
        
        # Mock weather response
        mock_weather_response = type('Response', (), {
            'status_code': 200,
            'json': lambda: {
                'weather': [{
                    'main': 'Clear',
                    'description': 'clear sky',
                    'icon': '01d'
                }],
                'main': {
                    'temp': 75.0,
                    'humidity': 50
                },
                'sys': {
                    'sunrise': 1600000000,
                    'sunset': 1600040000
                },
                'timezone': -14400
            }
        })
        
        mock_get.side_effect = [mock_geocode_response, mock_weather_response]
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('weather:api_weather'), {'city': 'New York'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['country'], 'US')
        self.assertEqual(data['city'], 'New York, NY, USA')
        self.assertEqual(data['weather_condition'], 'Clear')
        self.assertEqual(data['temp'], 75.0)
        self.assertEqual(data['humidity'], 50)

    def test_get_weather_missing_city(self):
        """Test weather API with missing city parameter"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('weather:api_weather'))
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'query parameter is required')

    @patch('weather.views.requests.get')
    def test_get_weather_geocode_failure(self, mock_get):
        """Test weather API with geocode failure"""
        mock_response = type('Response', (), {
            'status_code': 500,
            'json': lambda: {}
        })
        mock_get.return_value = mock_response
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('weather:api_weather'), {'city': 'New York'})
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'failed to geocode address')

    @patch('weather.views.requests.get')
    def test_get_weather_no_addresses(self, mock_get):
        """Test weather API with no addresses found"""
        mock_response = type('Response', (), {
            'status_code': 200,
            'json': lambda: {'addresses': []}
        })
        mock_get.return_value = mock_response
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('weather:api_weather'), {'city': 'Invalid City'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['error'], 'No addresses found')
