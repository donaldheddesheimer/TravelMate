from django.urls import path
from . import views

urlpatterns = [
    path('weather/', views.weather_forecast, name='weather_api'),
    path('places/', views.place_search, name='places_api'),
    path('places/autocomplete/', views.place_autocomplete, name='places_autocomplete'),
    path('places/<str:place_id>/', views.place_details, name='place_details'),
    path('chat/', views.chatbot, name='chatbot_api'),
]