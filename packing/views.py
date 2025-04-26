from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import ValidationError
import json
from datetime import date

from api.services.packing import PackingListGenerator
from trips.models import Trip
from .models import PackingList, PackingItem


@login_required
def packing_list_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    packing_list, created = PackingList.objects.get_or_create(trip=trip)

    # Organize items by category
    items_by_category = {}
    for item in packing_list.items.all().order_by('category', 'name'):
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)

    return render(request, 'packing/packing_list.html', {
        'trip': trip,
        'packing_list': packing_list,
        'items_by_category': items_by_category,
        'category_choices': PackingItem.CATEGORY_CHOICES
    })


@login_required
@require_POST
def generate_packing_list(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    packing_list, _ = PackingList.objects.get_or_create(trip=trip)

    try:
        # Clear existing items (keep custom items if you prefer)
        packing_list.items.filter(custom_added=False).delete()

        # Generate new items
        raw = PackingListGenerator.generate_packing_list(trip)
        data = json.loads(raw)

        for cat in data.get('categories', []):
            # Normalize category name
            code = cat.get('name', '').upper().replace(' ', '_')
            if code not in dict(PackingItem.CATEGORY_CHOICES).keys():
                code = 'MISC'

            for it in cat.get('items', []):
                PackingItem.objects.create(
                    packing_list=packing_list,
                    name=it.get('name', '').strip(),
                    category=code,
                    quantity=max(1, int(it.get('quantity', 1))),
                    is_essential=bool(it.get('essential', True)),
                    notes=it.get('notes', '') or '',
                    for_day=date.fromisoformat(it['for_day']) if it.get('for_day') else None,
                    custom_added=False
                )

        packing_list.generated = True
        packing_list.save()

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def add_custom_item(request, trip_id):
    try:
        payload = json.loads(request.body)
        trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
        packing_list, _ = PackingList.objects.get_or_create(trip=trip)

        item = PackingItem.objects.create(
            packing_list=packing_list,
            name=payload.get('name', '').strip(),
            category=payload.get('category', 'MISC'),
            quantity=max(1, int(payload.get('quantity', 1))),
            is_essential=bool(payload.get('is_essential', False)),
            notes=payload.get('notes', ''),
            custom_added=True
        )

        return JsonResponse({
            'status': 'success',
            'item': {
                'id': item.id,
                'name': item.name,
                'category': item.get_category_display(),
                'quantity': item.quantity,
                'is_essential': item.is_essential,
                'notes': item.notes,
                'for_day': item.for_day.isoformat() if item.for_day else None
            }
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST", "DELETE"])
def update_packing_item(request, item_id):
    item = get_object_or_404(
        PackingItem,
        pk=item_id,
        packing_list__trip__user=request.user
    )

    if request.method == 'DELETE':
        item.delete()
        return JsonResponse({'status': 'success'})

    try:
        data = json.loads(request.body)
        if 'name' in data:
            item.name = data['name'].strip()
        if 'category' in data:
            item.category = data['category']
        if 'quantity' in data:
            item.quantity = max(1, int(data['quantity']))
        if 'is_essential' in data:
            item.is_essential = bool(data['is_essential'])
        if 'notes' in data:
            item.notes = data['notes'].strip()
        if 'for_day' in data:
            item.for_day = date.fromisoformat(data['for_day']) if data['for_day'] else None

        item.save()
        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def toggle_item_completion(request, item_id):
    item = get_object_or_404(
        PackingItem,
        pk=item_id,
        packing_list__trip__user=request.user
    )
    item.completed = not item.completed
    item.save()
    return JsonResponse({
        'status': 'success',
        'completed': item.completed
    })


@login_required
@require_POST
def edit_packing_item(request, item_id):
    try:
        item = PackingItem.objects.get(id=item_id)
        if item.packing_list.trip.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
            
        payload = json.loads(request.body)
        
        # Update the item
        item.name = payload.get('name', item.name).strip()
        item.category = payload.get('category', item.category)
        item.quantity = max(1, int(payload.get('quantity', item.quantity)))
        item.is_essential = bool(payload.get('is_essential', item.is_essential))
        item.notes = payload.get('notes', item.notes)
        item.save()

        return JsonResponse({
            'status': 'success',
            'item': {
                'id': item.id,
                'name': item.name,
                'category': item.get_category_display(),
                'quantity': item.quantity,
                'is_essential': item.is_essential,
                'notes': item.notes,
                'for_day': item.for_day.isoformat() if item.for_day else None
            }
        })

    except PackingItem.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)