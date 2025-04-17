from django.urls import path
from . import views

app_name = "chatbot"

urlpatterns = [
    path('', views.chat, name='chatbot'),
    path('chat/', views.chat_view, name='chat_view'),
]
