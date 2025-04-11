# tips/views.py
from django.shortcuts import render, get_object_or_404
from trips.models import Trip
import requests
from django.conf import settings


def destination_tips(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    # Call an external API for travel tips (example)
    # You might use a service like Geonames or a custom database
    tips = [
        {"category": "Cultural", "tip": "In this destination, it's customary to greet with a bow."},
        {"category": "Safety", "tip": "Avoid displaying expensive items in public areas."},
        {"category": "Transportation", "tip": "The metro system is the most efficient way to get around."},
    ]

    context = {
        'trip': trip,
        'tips': tips,
        'active_tab': 'tips'
    }
    return render(request, 'tips/destination.html', context)