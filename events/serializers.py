from rest_framework import serializers

from .models import Event, RSVP


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event CRUD — host is set automatically from the request."""

    class Meta:
        model = Event
        fields = ("id", "title", "description", "date_time", "location", "created_at")
        read_only_fields = ("id", "created_at")


class PublicEventSerializer(serializers.ModelSerializer):
    """Read-only serializer for public event details — no host info, no RSVPs."""

    class Meta:
        model = Event
        fields = ("id", "title", "description", "date_time", "location")
        read_only_fields = fields


class RSVPSerializer(serializers.ModelSerializer):
    """Validates guest RSVP submission."""

    class Meta:
        model = RSVP
        fields = ("guest_name", "guest_email", "status", "plus_one_count", "guest_id")

    def validate_guest_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Guest name cannot be blank.")
        return value

    def create(self, validated_data):
        event = self.context["event"]
        guest_id = validated_data.pop("guest_id")
        rsvp, _ = RSVP.objects.update_or_create(
            event=event,
            guest_id=guest_id,
            defaults=validated_data,
        )
        return rsvp


class RSVPListSerializer(serializers.ModelSerializer):
    """Read-only serializer for the host's view of individual RSVPs."""

    class Meta:
        model = RSVP
        fields = ("id", "guest_name", "guest_email", "status", "plus_one_count", "guest_id", "created_at")
        read_only_fields = fields

