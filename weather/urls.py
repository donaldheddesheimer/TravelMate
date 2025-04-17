from django.urls import path
from .views import get_weather_view
urlpatterns = [
    path('weather/', get_weather_view, name="get_weather_view")
]