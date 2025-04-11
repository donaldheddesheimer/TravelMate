from django import forms
from trips.models import Trip

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['destination', 'date_leaving', 'date_returning']
        widgets = {
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter destination',
                'list': 'destinationOptions'
            }),
            'date_leaving': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'date_returning': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }