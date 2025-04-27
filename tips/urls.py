# tips/urls.py
from django.urls import path
from . import views

app_name = 'tips'

urlpatterns = [
    # URL to view the tips list for a specific trip
    path('<int:trip_id>/', views.travel_tips_view, name='list'),

    # URL to trigger the generation of tips for a specific trip
    path('<int:trip_id>/generate/', views.generate_travel_tips, name='generate'),

    # No URLs needed for adding, updating, deleting, or toggling items
]