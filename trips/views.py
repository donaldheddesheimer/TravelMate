# trips/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Trip
from .forms import TripForm

@login_required
def trip_list(request):
    trips = Trip.objects.filter(user=request.user)
    return render(request, 'trips/trip_list.html', {'trips': trips})

@login_required
def trip_create(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            trip.save()
            # Process activities
            activities = request.POST.getlist('activities')
            if activities:
                # Filter out empty activities
                valid_activities = [act.strip() for act in activities if act.strip()]
                if valid_activities:
                    trip.activities = "\n".join(valid_activities)
                    trip.save()
            return redirect('trips:list')
    else:
        form = TripForm()
    return render(request, 'trips/trip_create.html', {'form': form})

@login_required
def trip_dashboard(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    context = {
        'trip': trip,
        'active_tab': 'overview'
    }
    return render(request, 'trips/dashboard.html', context)

@login_required
def trip_edit(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            form.save()
            return redirect('trips:dashboard', trip_id=trip.id)
    else:
        form = TripForm(instance=trip)
    return render(request, 'trips/trip_edit.html', {'form': form, 'trip': trip})

@login_required
def trip_delete(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        trip.delete()
        return redirect('trips:list')
    return render(request, 'trips/trip_confirm_delete.html', {'trip': trip})