from django.db import models
from trips.models import Trip

class PackingList(models.Model):
    trip = models.OneToOneField(
        Trip,
        on_delete=models.CASCADE,
        related_name='packing_list'
    )
    generated = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_updated']

    def __str__(self):
        return f"Packing list for {self.trip.destination}"


class PackingItem(models.Model):
    CATEGORY_CHOICES = [
        ('CLOTHING', 'Clothing'),
        ('TOILETRIES', 'Toiletries'),
        ('ELECTRONICS', 'Electronics'),
        ('DOCUMENTS', 'Documents'),
        ('MISC', 'Miscellaneous'),
    ]

    packing_list = models.ForeignKey(
        PackingList,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.PositiveSmallIntegerField(default=1)
    is_essential = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    for_day = models.DateField(null=True, blank=True)
    custom_added = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} (x{self.quantity})"