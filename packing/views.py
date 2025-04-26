# packing/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import ValidationError
import json
from datetime import date
import logging # Import logging

# Corrected import path for PackingListGenerator based on your structure
from api.services.packing import PackingListGenerator
from trips.models import Trip
from .models import PackingList, PackingItem
# Import the new weather service function
from weather.services import fetch_and_summarize_weather

logger = logging.getLogger(__name__) # Add logger


@login_required
def packing_list_view(request, trip_id):
    # ... (keep existing code) ...
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    packing_list, created = PackingList.objects.get_or_create(trip=trip)

    items_by_category = {}
    # Use the related manager directly for efficiency
    for item in packing_list.items.all().order_by('category', 'name'):
        # Use get_category_display() for readable names if using choices
        category_display = item.get_category_display()
        if category_display not in items_by_category:
            items_by_category[category_display] = []
        items_by_category[category_display].append(item)

    # Get display names for choices to pass to template if needed elsewhere
    category_choices_dict = dict(PackingItem.CATEGORY_CHOICES)

    return render(request, 'packing/packing_list.html', {
        'trip': trip,
        'packing_list': packing_list,
        'items_by_category': items_by_category,
        'category_choices': PackingItem.CATEGORY_CHOICES, # Pass original choices for dropdown
        'category_choices_dict': category_choices_dict, # Pass display names if needed
        'active_tab': 'packing_list' # Assuming you have tabs
    })


@login_required
@require_POST
def generate_packing_list(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    packing_list, _ = PackingList.objects.get_or_create(trip=trip)

    # --- Fetch Weather Summary ---
    try:
        weather_summary = fetch_and_summarize_weather(
            destination=trip.destination,
            start_date=trip.date_leaving,
            end_date=trip.date_returning
        )
        logger.info(f"Weather summary for Trip {trip_id}: {weather_summary}")
    except Exception as e:
        logger.error(f"Failed to fetch weather for trip {trip_id}: {e}", exc_info=True)
        # Decide if you want to proceed without weather or return an error
        # Option 1: Proceed with a placeholder
        weather_summary = "Weather information could not be retrieved."
        # Option 2: Return error immediately (uncomment below)
        # return JsonResponse({
        #     'status': 'error',
        #     'message': f"Failed to retrieve weather information: {e}"
        # }, status=500)

    # --- Generate Packing List ---
    try:
        # Generate new items, passing the weather summary
        # Ensure PackingListGenerator expects weather_summary
        raw_packing_list_json = PackingListGenerator.generate_packing_list(trip, weather_summary)

        # Log the raw response for debugging if needed
        # logger.debug(f"Raw OpenAI response for trip {trip_id}: {raw_packing_list_json}")

        packing_data = json.loads(raw_packing_list_json)

        # Handle potential errors returned within the JSON from the generator itself
        if isinstance(packing_data, dict) and "error" in packing_data:
             logger.error(f"Packing list generation failed (reported by generator): {packing_data['error']}")
             return JsonResponse({
                 'status': 'error',
                 'message': f"AI generation failed: {packing_data['error']}"
                 }, status=500)

        # --- Save Packing List Items ---
        # Clear existing AI-generated items before adding new ones
        packing_list.items.filter(custom_added=False).delete()

        items_created_count = 0
        for category_data in packing_data.get('categories', []):
            category_name = category_data.get('name', 'Miscellaneous') # Default category name
            # Map category name to your choices enum/code
            category_code = 'MISC' # Default
            normalized_name = category_name.upper().replace(' ', '_').replace('-', '_')
            # Simple mapping (improve if needed)
            for code, name in PackingItem.CATEGORY_CHOICES:
                 # Match based on code or name (flexible)
                 if normalized_name == code or normalized_name == name.upper().replace(' ', '_'):
                     category_code = code
                     break

            for item_data in category_data.get('items', []):
                item_name = item_data.get('name', '').strip()
                if not item_name:
                    logger.warning(f"Skipping item with no name in category '{category_name}'")
                    continue # Skip items without a name

                # Handle potential date parsing errors
                item_for_day = None
                if item_data.get('for_day'):
                    try:
                        # Attempt ISO format first (YYYY-MM-DD)
                        item_for_day = date.fromisoformat(item_data['for_day'])
                    except (ValueError, TypeError):
                         # Add more formats if needed, or log a warning
                         logger.warning(f"Could not parse date '{item_data['for_day']}' for item '{item_name}'. Skipping date.")
                         pass # Keep item_for_day as None

                PackingItem.objects.create(
                    packing_list=packing_list,
                    name=item_name,
                    category=category_code, # Use the mapped code
                    quantity=max(1, int(item_data.get('quantity', 1))), # Ensure quantity is at least 1
                    is_essential=bool(item_data.get('essential', False)), # Default to False if not specified
                    notes=item_data.get('notes', '') or '',
                    for_day=item_for_day,
                    custom_added=False # Mark as AI generated
                )
                items_created_count += 1

        packing_list.generated = True # Mark the list as having been generated
        packing_list.save()

        logger.info(f"Successfully generated and saved {items_created_count} packing items for trip {trip_id}.")
        return JsonResponse({'status': 'success', 'message': 'Packing list generated successfully!'})

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from OpenAI for trip {trip_id}: {e}\nRaw response: {raw_packing_list_json}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to understand the response from the AI generator. Invalid format.'
        }, status=500)
    except ValidationError as e:
        logger.error(f"Validation error saving packing item for trip {trip_id}: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f"Error saving packing item: {e}"
        }, status=400)
    except Exception as e:
        # Catch any other unexpected errors during generation or saving
        logger.error(f"Unexpected error generating packing list for trip {trip_id}: {e}", exc_info=True) # Log traceback
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {e}'
        }, status=500)


# ... (keep other views: add_custom_item, update_packing_item, toggle_item_completion) ...

@login_required
@require_POST
def add_custom_item(request, trip_id):
    try:
        payload = json.loads(request.body)
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
        packing_list, _ = PackingList.objects.get_or_create(trip=trip)

        item_name = payload.get('name', '').strip()
        category_code = payload.get('category', 'MISC') # Expecting code from select dropdown

        if not item_name:
            return JsonResponse({'status': 'error', 'message': 'Item name cannot be empty.'}, status=400)

        # Validate category code
        if category_code not in dict(PackingItem.CATEGORY_CHOICES):
            logger.warning(f"Invalid category code '{category_code}' received for custom item. Defaulting to MISC.")
            category_code = 'MISC'

        item = PackingItem.objects.create(
            packing_list=packing_list,
            name=item_name,
            category=category_code,
            quantity=max(1, int(payload.get('quantity', 1))),
            is_essential=bool(payload.get('is_essential', False)),
            notes=payload.get('notes', ''),
            custom_added=True
        )

        return JsonResponse({
            'status': 'success',
            # Return data needed to potentially update UI without full reload
            'item': {
                'id': item.id,
                'name': item.name,
                'category_code': item.category,
                'category_display': item.get_category_display(),
                'quantity': item.quantity,
                'is_essential': item.is_essential,
                'notes': item.notes,
                'completed': item.completed,
                'for_day': item.for_day.isoformat() if item.for_day else None,
                'custom_added': item.custom_added,
            }
        })

    except json.JSONDecodeError:
         return JsonResponse({'status': 'error', 'message': 'Invalid request format.'}, status=400)
    except (ValueError, TypeError) as e:
         logger.error(f"Error processing custom item data: {e}", exc_info=True)
         return JsonResponse({'status': 'error', 'message': 'Invalid data provided (e.g., quantity must be a number).'}, status=400)
    except Exception as e:
        logger.error(f"Error adding custom item for trip {trip_id}: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {e}'
        }, status=500)


@login_required
@require_http_methods(["POST", "DELETE"]) # Allow POST for updates
def update_packing_item(request, item_id):
    item = get_object_or_404(
        PackingItem,
        pk=item_id,
        packing_list__trip__user=request.user # Ensure user owns the item via trip
    )

    if request.method == 'DELETE':
        try:
            item_name = item.name # For logging
            item.delete()
            logger.info(f"Deleted packing item '{item_name}' (ID: {item_id})")
            return JsonResponse({'status': 'success', 'message': 'Item deleted.'})
        except Exception as e:
             logger.error(f"Error deleting item {item_id}: {e}", exc_info=True)
             return JsonResponse({'status': 'error', 'message': 'Failed to delete item.'}, status=500)

    # --- Handle POST for updates ---
    # This part assumes you might implement inline editing later.
    # If you only use the modal (add_custom_item), this update part might not be strictly needed yet.
    try:
        data = json.loads(request.body)
        updated_fields = []

        # Update fields only if they are present in the request payload
        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                 return JsonResponse({'status': 'error', 'message': 'Item name cannot be empty.'}, status=400)
            if item.name != new_name:
                 item.name = new_name
                 updated_fields.append('name')

        if 'category' in data:
            new_category = data['category']
             # Validate category code
            if new_category not in dict(PackingItem.CATEGORY_CHOICES):
                 logger.warning(f"Invalid category code '{new_category}' received during update. Ignoring change.")
            elif item.category != new_category:
                 item.category = new_category
                 updated_fields.append('category')

        if 'quantity' in data:
            try:
                new_quantity = max(1, int(data['quantity']))
                if item.quantity != new_quantity:
                    item.quantity = new_quantity
                    updated_fields.append('quantity')
            except (ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': 'Quantity must be a valid number.'}, status=400)

        if 'is_essential' in data:
            new_essential = bool(data['is_essential'])
            if item.is_essential != new_essential:
                item.is_essential = new_essential
                updated_fields.append('is_essential')

        if 'notes' in data:
             new_notes = data['notes'].strip()
             if item.notes != new_notes:
                 item.notes = new_notes
                 updated_fields.append('notes')

        if 'for_day' in data:
            new_for_day = None
            if data['for_day']:
                try:
                    new_for_day = date.fromisoformat(data['for_day'])
                except (ValueError, TypeError):
                     return JsonResponse({'status': 'error', 'message': 'Invalid date format for for_day (use YYYY-MM-DD).'}, status=400)
            if item.for_day != new_for_day:
                item.for_day = new_for_day
                updated_fields.append('for_day')

        if updated_fields:
            item.save()
            logger.info(f"Updated packing item {item_id}. Fields changed: {', '.join(updated_fields)}")
            # Return updated item details
            return JsonResponse({
                'status': 'success',
                'message': 'Item updated.',
                 'item': { # Return updated data
                    'id': item.id,
                    'name': item.name,
                    'category_code': item.category,
                    'category_display': item.get_category_display(),
                    'quantity': item.quantity,
                    'is_essential': item.is_essential,
                    'notes': item.notes,
                    'completed': item.completed,
                    'for_day': item.for_day.isoformat() if item.for_day else None,
                    'custom_added': item.custom_added,
                }
            })
        else:
             return JsonResponse({'status': 'success', 'message': 'No changes detected.'}) # Or return 304 Not Modified?


    except json.JSONDecodeError:
         return JsonResponse({'status': 'error', 'message': 'Invalid request format.'}, status=400)
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred during update: {e}'
        }, status=500)


@login_required
@require_POST
def toggle_item_completion(request, item_id):
    item = get_object_or_404(
        PackingItem,
        pk=item_id,
        packing_list__trip__user=request.user
    )
    try:
        item.completed = not item.completed
        item.save()
        logger.debug(f"Toggled completion for item {item_id} to {item.completed}")
        return JsonResponse({
            'status': 'success',
            'completed': item.completed # Send back the new state
        })
    except Exception as e:
        logger.error(f"Error toggling completion for item {item_id}: {e}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to update item completion status.'
        }, status=500)