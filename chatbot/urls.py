from django.urls import path
from . import views
app_name = 'chatbot'

urlpatterns = [
    path('<int:trip_id>/', views.chat, name='chatbot'),
    path('<int:trip_id>/chat/', views.chat_view, name='chat_view'),
]