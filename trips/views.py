from django.shortcuts import render, redirect
from .models import Trip
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def add_trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            trip.save()
            return redirect('trips:list')  # Change if needed
    else:
        form = TripForm()
    return render(request, 'trips/add_trip.html', {'form': form})

def trip_list(request):
    if not request.user.is_authenticated:
        return redirect('login')  # or your login URL name

    trips = Trip.objects.filter(user=request.user)
    return render(request, 'trips/trip_list.html', {'trips': trips})



def trip_create(request):
    if request.method == 'POST':
        # Process form data here (for now, you can print it)
        destination = request.POST.get('destination')
        date_leaving = request.POST.get('date_leaving')
        date_return = request.POST.get('date_return')
        print("Destination:", destination)
        print("Leaving:", date_leaving)
        print("Returning:", date_return)
        # Redirect after processing
        return redirect('trips:list')

    # For GET requests, render the form
    return render(request, 'trips/trip_create.html')
