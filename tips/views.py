# tips/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import logging

from api.services.tips import TravelTipsGenerator # Import the new generator
from trips.models import Trip
from .models import TravelTips, TipItem # Import the new models

logger = logging.getLogger(__name__)

@login_required
def travel_tips_view(request, trip_id):
    """Displays the generated travel tips for a trip."""
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    travel_tips, created = TravelTips.objects.get_or_create(trip=trip)

    tips_by_category = {}
    # Group tips by category display name
    for item in travel_tips.items.all().order_by('category', 'id'):
        category_display = item.get_category_display()
        if category_display not in tips_by_category:
            tips_by_category[category_display] = []
        tips_by_category[category_display].append(item)

    # Map category codes to display names for potential use
    category_choices_dict = dict(TipItem.CATEGORY_CHOICES)

    return render(request, 'tips/travel_tips.html', {
        'trip': trip,
        'travel_tips': travel_tips, # The main TravelTips object
        'tips_by_category': tips_by_category, # Grouped items for display
        'category_choices_dict': category_choices_dict,
        'active_tab': 'travel_tips' # For dashboard navigation highlighting
    })


@login_required
@require_POST
def generate_travel_tips(request, trip_id):
    """Generates new travel tips using the AI service."""
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    travel_tips, _ = TravelTips.objects.get_or_create(trip=trip)

    # --- Generate Travel Tips (No weather needed here) ---
    try:
        raw_tips_json = TravelTipsGenerator.generate_travel_tips(trip)
        tips_data = json.loads(raw_tips_json)

        # Handle errors reported by the generator itself
        if isinstance(tips_data, dict) and "error" in tips_data:
             logger.error(f"Travel tips generation failed (reported by generator): {tips_data['error']}")
             return JsonResponse({
                 'status': 'error',
                 'message': f"AI generation failed: {tips_data['error']}"
                 }, status=500)

        # --- Save Travel Tips ---
        # Clear existing tips before adding new ones
        travel_tips.items.all().delete()

        tips_created_count = 0
        category_map = { # Map display names from AI to model codes
            'Cultural Advice': 'CULTURAL',
            'Local Information': 'LOCAL_INFO',
            'Must Have Items': 'MUST_HAVE',
        }

        for category_data in tips_data.get('categories', []):
            category_name = category_data.get('name', 'General Tips')
            # Map the received name to one of our defined category codes
            category_code = category_map.get(category_name, 'GENERAL') # Default to GENERAL

            for item_data in category_data.get('items', []):
                tip_content = item_data.get('tip', '').strip()
                if not tip_content:
                    logger.warning(f"Skipping empty tip in category '{category_name}' for trip {trip_id}")
                    continue # Skip items without content

                TipItem.objects.create(
                    travel_tips=travel_tips,
                    category=category_code,
                    content=tip_content
                )
                tips_created_count += 1

        travel_tips.generated = True
        travel_tips.save()

        logger.info(f"Successfully generated and saved {tips_created_count} travel tips for trip {trip_id}.")
        return JsonResponse({'status': 'success', 'message': 'Travel tips generated successfully!'})

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from AI for tips (Trip {trip_id}): {e}\nRaw response: {raw_tips_json}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to understand the response from the AI generator. Invalid format.'
        }, status=500)
    except Exception as e:
        logger.error(f"Unexpected error generating travel tips for trip {trip_id}: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {e}'
        }, status=500)