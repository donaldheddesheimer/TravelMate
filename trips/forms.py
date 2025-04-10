from django import forms
from trips.models import Trip

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['destination', 'date_leaving', 'date_return']
        widgets = {
            'date_leaving': forms.DateInput(attrs={'type': 'date'}),
            'date_return': forms.DateInput(attrs={'type': 'date'}),
        }