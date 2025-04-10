# TravelMate/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('trips/', include('trips.urls', namespace='trips')),
    path('', include('home.urls', namespace='home')),
]