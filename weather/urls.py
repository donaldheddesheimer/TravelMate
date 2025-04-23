from django.urls import path
from .views import get_weather_view
app_name = 'weather'
urlpatterns = [
    path('weather/', get_weather_view, name="get_weather_view"),
    path('<int:trip_id>/forecast/', get_weather_view, name="forecast")
]