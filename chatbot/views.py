# # chatbot/views.py
# from django.shortcuts import render, get_object_or_404
# from trips.models import Trip
# import openai
# from django.conf import settings
#
#
# def trip_assistant(request, trip_id):
#     trip = get_object_or_404(Trip, id=trip_id, user=request.user)
#     chat_history = []
#
#     if request.method == 'POST':
#         user_message = request.POST.get('message')
#
#         # Initialize OpenAI client
#         openai.api_key = settings.OPENAI_API_KEY
#
#         # Create a prompt with trip details
#         prompt = f"""
#         You are a travel assistant helping with a trip to {trip.destination} from {trip.date_leaving} to {trip.date_returning}.
#         Planned activities: {trip.activities or 'Not specified'}
#
#         User question: {user_message}
#         """
#
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": prompt}]
#         )
#
#         chat_history.append({"role": "user", "content": user_message})
#         chat_history.append({"role": "assistant", "content": response.choices[0].message.content})
#
#     context = {
#         'trip': trip,
#         'chat_history': chat_history,
#         'active_tab': 'chatbot'
#     }
#     return render(request, 'chatbot/assistant.html', context)