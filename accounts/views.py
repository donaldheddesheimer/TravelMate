from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account is created {username}!')
            return redirect('account.login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'account/signup.html', {'form': form})

@login_required()
def profile(request):
    return render(request, 'account/profile.html')

@login_required
def orders(request):
    template_data = {}
    template_data['title'] = 'Orders'
    template_data['orders'] = request.user.order_set.all()
    return render(request, 'account/orders.html', {'template_data': template_data})