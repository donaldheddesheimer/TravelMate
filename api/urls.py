from django.urls import path
from . import views

urlpatterns = [
    path('weather/', views.weather_forecast, name='weather_api'),
    path('places/', views.place_search, name='places_api'),
    path('chat/', views.chatbot, name='chatbot_api'),
]