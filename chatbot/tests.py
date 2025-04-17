from django.test import TestCase
from django.contrib.auth.models import User
from trips.models import Trip
from .models import ChatMessage


class ChatbotTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.trip = Trip.objects.create(
            user=self.user,
            destination="Paris",
            date_leaving="2023-12-01",
            date_returning="2023-12-10"
        )

    def test_chat_creation(self):
        msg = ChatMessage.objects.create(
            trip=self.trip,
            user=self.user,
            message="Test",
            response="Test response"
        )
        self.assertEqual(str(msg), "testuser - Paris")