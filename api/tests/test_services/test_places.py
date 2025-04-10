from django.test import TestCase
from unittest.mock import patch
from api.services.places import GooglePlacesService

class GooglePlacesServiceTest(TestCase):
    @patch('requests.get')
    def test_search_places(self, mock_get):
        # Mock API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "results": [{"name": "Eiffel Tower"}]
        }

        # Call the service
        result = GooglePlacesService.search_places("tourist attractions", "48.8566,2.3522")
        print(result)
        # Assertions
        self.assertIn("results", result)
        self.assertEqual(result["results"][0]["name"], "Eiffel Tower")
        mock_get.assert_called_once()  # Verify API was called