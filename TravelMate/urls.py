# TravelMate/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('trips/', include('trips.urls', namespace='trips')),
    path('', include('home.urls', namespace='home')),
    path('api/', include('api.urls', namespace='api')),
    path('trips/<int:trip_id>/', include('chatbot.urls')),
    path('weather/', include("weather.urls")),
    path('tips/', include('tips.urls')),
    path('packing/', include('packing.urls', namespace='packing')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)