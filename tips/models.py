# tips/models.py
from django.db import models
from trips.models import Trip

class TravelTips(models.Model):
    """Stores a collection of generated tips for a specific trip."""
    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='travel_tips' # Use travel_tips to access from Trip
    )
    generated = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_updated']
        verbose_name_plural = "Travel Tips" # Correct plural name in admin

    def __str__(self):
        return f"Travel Tips for {self.trip.destination}"


class TipItem(models.Model):
    """Represents a single travel tip."""
    CATEGORY_CHOICES = [
        ('CULTURAL', 'Cultural Advice'),
        ('LOCAL_INFO', 'Local Information'),
        ('MUST_HAVE', 'Must Have Items'), # Keeping this as requested
        ('GENERAL', 'General Tips'),     # Adding a fallback general category
    ]

    travel_tips = models.ForeignKey(
        TravelTips,
        on_delete=models.CASCADE,
        related_name='items' # Use items to access from TravelTips instance
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='GENERAL' # Default category if AI response is unexpected
    )
    content = models.TextField() # The actual tip text

    # Removed: name, quantity, is_essential, notes, for_day, custom_added, completed

    class Meta:
        ordering = ['category', 'id'] # Order by category, then by creation order

    def __str__(self):
        # Limit the string representation length
        return f"{self.get_category_display()}: {self.content[:50]}..."