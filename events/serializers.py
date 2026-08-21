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
    """Validates and creates a guest RSVP submission."""

    class Meta:
        model = RSVP
        fields = ("guest_name", "status", "plus_one_count", "guest_id")

    def validate_guest_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Guest name cannot be blank.")
        return value

    def validate(self, data):
        event = self.context["event"]
        guest_id = data.get("guest_id")

        if RSVP.objects.filter(event=event, guest_id=guest_id).exists():
            raise serializers.ValidationError(
                {"guest_id": "You have already submitted an RSVP for this event."}
            )
        return data

    def create(self, validated_data):
        validated_data["event"] = self.context["event"]
        return super().create(validated_data)


class RSVPListSerializer(serializers.ModelSerializer):
    """Read-only serializer for the host's view of individual RSVPs."""

    class Meta:
        model = RSVP
        fields = ("id", "guest_name", "status", "plus_one_count", "guest_id", "created_at")
        read_only_fields = fields

