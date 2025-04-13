from django.test import TestCase
from unittest.mock import patch
from .services.weather import WeatherService


class WeatherAPITests(TestCase):
    @patch('requests.get')
    def test_get_forecast(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'temp': 25}

        result = WeatherService.get_forecast(40.71, -74.01, '2023-12-01')
        self.assertEqual(result['temp'], 25)