# packing/views.py
from django.shortcuts import render, get_object_or_404, redirect
from trips.models import Trip, PackingItem
from django.contrib.auth.decorators import login_required


@login_required
def packing_list(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if request.method == 'POST':
        # Handle form submission for new items
        item_name = request.POST.get('item_name')
        category = request.POST.get('category')
        if item_name:
            PackingItem.objects.create(
                trip=trip,
                name=item_name,
                category=category
            )
            return redirect('packing:list', trip_id=trip.id)

    items = trip.packing_items.all()

    context = {
        'trip': trip,
        'items': items,
        'active_tab': 'packing'
    }
    return render(request, 'packing/list.html', context)