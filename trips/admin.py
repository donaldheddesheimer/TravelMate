# trips/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html

# Import models from the current app (trips)
from .models import Trip, PackingItem

# --- Inline Configuration for PackingItem within Trip Admin ---

class PackingItemInline(admin.TabularInline):
    """
    Allows editing PackingItems directly within the Trip admin page.
    'TabularInline' displays them in a compact table format.
    """
    model = PackingItem
    fields = ('name', 'category', 'is_packed', 'notes') # Fields to show in the inline form
    extra = 1 # Number of empty extra forms to display
    # classes = ['collapse'] # Optionally make the inline section collapsible

# --- Admin Configuration for the Trip Model ---

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the Trip model.
    """
    # Columns to display in the Trip list view
    list_display = ('destination', 'user_link', 'date_leaving', 'date_returning', 'created_at')
    # Fields to allow filtering by in the right sidebar
    list_filter = ('user', 'date_leaving', 'date_returning', 'created_at')
    # Fields to enable searching within
    search_fields = ('destination', 'user__username', 'user__email', 'activities', 'notes')
    # Fields that should not be editable in the admin detail view
    readonly_fields = ('created_at', 'updated_at')
    # Embed the PackingItemInline configuration
    inlines = [PackingItemInline]
    # Which fields in list_display should link to the detail view
    list_display_links = ('destination',) # Link from destination by default

    # Organize fields in the Trip add/change form
    fieldsets = (
        (None, {
            'fields': ('user', 'destination')
        }),
        ('Dates', {
            'fields': ('date_leaving', 'date_returning')
        }),
        ('Details', {
            'fields': ('activities', 'notes'),
            'classes': ('collapse',) # Make this section collapsible
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Method to create a clickable link to the user admin page
    def user_link(self, obj):
        if obj.user:
            # Use reverse to get the URL for the specific user's admin change page
            user_admin_url = reverse("admin:auth_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', user_admin_url, obj.user.username)
        return "N/A" # Or handle case where user might be null if allowed
    user_link.short_description = 'User' # Column header
    user_link.admin_order_field = 'user' # Allow sorting by user

# --- Admin Configuration for the PackingItem Model ---

@admin.register(PackingItem)
class PackingItemAdmin(admin.ModelAdmin):
    """
    Customizes the admin interface for the PackingItem model (standalone view).
    """
    list_display = ('name', 'trip_link', 'category', 'is_packed')
    list_filter = ('trip__user', 'category', 'is_packed', 'trip__destination') # Filter by user via trip
    search_fields = ('name', 'category', 'trip__destination', 'trip__user__username')
    list_editable = ('is_packed',) # Allow editing 'is_packed' directly in the list view

    # Method to create a clickable link to the trip admin page
    def trip_link(self, obj):
        if obj.trip:
            trip_admin_url = reverse("admin:trips_trip_change", args=[obj.trip.id])
            return format_html('<a href="{}">{}</a>', trip_admin_url, obj.trip.destination)
        return "N/A"
    trip_link.short_description = 'Trip'
    trip_link.admin_order_field = 'trip'


# --- Custom Admin Configuration for the Built-in User Model ---

class CustomUserAdmin(BaseUserAdmin):
    """
    Enhances the default Django User admin to show Trip-related information.
    """
    # Add custom columns and relevant user fields to the list display
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'date_joined',      # Show when the user signed up
        'last_login',       # Show user's last activity
        'trip_count',       # Custom method below
        'view_trips_link'   # Custom method below
    )
    # Add date filters to the standard filters
    list_filter = BaseUserAdmin.list_filter + ('date_joined', 'last_login')
    # Allow searching by email in addition to username
    search_fields = BaseUserAdmin.search_fields + ('email',)

    # Method to calculate and display the number of trips for a user
    def trip_count(self, obj):
        # 'obj' is the User instance for the current row
        # Assumes the default related_name 'trip_set' from Trip.user ForeignKey
        return obj.trip_set.count()
    trip_count.short_description = 'Trips Created' # Column header text
    # Allow sorting by trip count (may require annotation depending on DB)
    # trip_count.admin_order_field = 'trip_count_annotation' # If you add annotation

    # Method to create a link to the Trip admin, filtered for the specific user
    def view_trips_link(self, obj):
        count = obj.trip_set.count()
        if count == 0:
            return "None" # Display text if the user has no trips
        # Construct the URL to the Trip admin changelist page
        # 'admin:app_label_model_name_changelist' is the pattern
        url = (
            reverse("admin:trips_trip_changelist")
            + f"?user__id__exact={obj.id}" # Add query parameter to filter by user ID
        )
        # Use format_html for safe HTML rendering
        return format_html('<a href="{}">View {} Trips</a>', url, count)
    view_trips_link.short_description = 'View User\'s Trips' # Column header text


# --- Unregister the Default User Admin and Register the Custom One ---

# It's necessary to unregister the default admin before registering a custom one
# Use a try/except block in case User is not registered (e.g., in some test setups)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Register the User model using our custom admin class
admin.site.register(User, CustomUserAdmin)

# Note: Trip and PackingItem are registered using the @admin.register decorator above,
# so no explicit admin.site.register calls are needed for them here.