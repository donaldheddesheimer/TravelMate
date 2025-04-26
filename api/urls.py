from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
    path('weather/', views.weather_forecast, name='weather_api'),
    path('places/', views.place_search, name='places_api'),
    path('places/autocomplete/', views.place_autocomplete, name='places_autocomplete'),
    path('places/<str:place_id>/', views.place_details, name='place_details'),
    path('chat/', views.chatbot, name='chatbot_api'),
    path('packing-list/<int:trip_id>/', views.generate_packing_list, name='packing_list_api'),
]