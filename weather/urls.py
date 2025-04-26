from django.urls import path
from .views import get_weather_view, forecast_view

app_name = 'weather'

urlpatterns = [
    path('api/weather/', get_weather_view, name="api_weather"),
    path('<int:trip_id>/', forecast_view, name="forecast"),
]