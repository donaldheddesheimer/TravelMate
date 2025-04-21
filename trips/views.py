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

            activities_list = request.POST.getlist('activities')
            valid_activities = [act.strip() for act in activities_list if act.strip()]
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
    existing_activities = []
    if trip.activities:
        existing_activities = [act for act in trip.activities.split('\n') if act.strip()]

    if request.method == 'POST':
        form = TripForm(request.POST, instance=trip)
        if form.is_valid():
            trip_instance = form.save(commit=False)

            activities_list = request.POST.getlist('activities')
            valid_activities = [act.strip() for act in activities_list if act.strip()]
            trip_instance.activities = "\n".join(valid_activities)

            trip_instance.save()
            return redirect('trips:dashboard', trip_id=trip.id)
        else:
            # If form is invalid, re-render with errors and original activities
            # (The 'existing_activities' list defined earlier is used here)
             pass # Fall through to render below

    else: # GET request
        form = TripForm(instance=trip)

    # Prepare context for both GET and invalid POST rendering
    context = {
        'form': form,
        'trip': trip,
        'existing_activities': existing_activities
    }
    return render(request, 'trips/trip_edit.html', context)


@login_required
def trip_delete(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        trip.delete()
        return redirect('trips:list')
    else:
        return redirect('trips:list')