from rest_framework import serializers

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event CRUD — host is set automatically from the request."""

    class Meta:
        model = Event
        fields = ("id", "title", "description", "date_time", "location", "created_at")
        read_only_fields = ("id", "created_at")
