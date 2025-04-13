from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ChatMessage
from trips.models import Trip
from api.services.ai import DeepSeekService
from .serializers import ChatMessageSerializer
from django.contrib.auth.decorators import login_required


@api_view(['POST'])
def chat(request, trip_id):
    try:
        trip = Trip.objects.get(pk=trip_id, user=request.user)
        user_message = request.data.get('message', '')

        # save user message
        ChatMessage.objects.create(
            trip=trip,
            user=request.user,
            message=user_message,
            is_user_message=True
        )

        # create prompt
        prompt = f"""
        Trip Context:
        - Destination: {trip.destination}
        - Dates: {trip.date_leaving} to {trip.date_returning}
        - Activities: {trip.activities or 'Not specified'}
        - User's question: {user_message}
        
        You are TravelMate AI, a helpful travel assistant. 
        Provide specific, actionable advice based on the trip details.
        """

        # get AI response
        ai_response = DeepSeekService.chat_completion([
            {"role": "system", "content": "You are a travel planning assistant"},
            {"role": "user", "content": prompt}
        ])

        # save response
        response_text = ai_response['choices'][0]['message']['content']
        ChatMessage.objects.create(
            trip=trip,
            user=request.user,
            message=response_text,
            response=response_text,
            is_user_message=False
        )

        return Response({'response': response_text})

    except Exception as e:
        return Response({'error': str(e)}, status=400)

@api_view(['GET'])
def chat_history(request, trip_id):
    messages = ChatMessage.objects.filter(
        trip_id=trip_id,
        user=request.user
    ).order_by('timestamp')
    serializer = ChatMessageSerializer(messages, many=True)
    return Response(serializer.data)

@login_required
def chat_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    messages = ChatMessage.objects.filter(trip=trip).order_by('timestamp')
    return render(request, 'chatbot/chat.html', {
        'trip': trip,
        'messages': messages
    })