from django.contrib import admin

from .models import Event, RSVP


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "host", "date_time", "location", "created_at")
    list_filter = ("date_time",)
    search_fields = ("title", "location")


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "event", "status", "plus_one_count", "created_at")
    list_filter = ("status",)
    search_fields = ("guest_name", "guest_id")
