from django.conf import settings
from django.db import models


class Event(models.Model):
    """An event created by a host."""

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    date_time = models.DateTimeField()
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class RSVP(models.Model):
    """A guest's RSVP to an event (no account required)."""

    STATUS_CHOICES = [
        ("yes", "Yes"),
        ("no", "No"),
        ("maybe", "Maybe"),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="rsvps",
    )
    guest_name = models.CharField(max_length=255)
    status = models.CharField(max_length=5, choices=STATUS_CHOICES)
    plus_one_count = models.PositiveIntegerField(default=0)
    guest_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "guest_id")
        verbose_name = "RSVP"
        verbose_name_plural = "RSVPs"

    def __str__(self):
        return f"{self.guest_name} — {self.get_status_display()} ({self.event.title})"
