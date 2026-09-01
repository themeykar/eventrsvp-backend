from django.db.models import Count, Q, Sum
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event, RSVP
from .serializers import (
    EventSerializer,
    PublicEventSerializer,
    RSVPListSerializer,
    RSVPSerializer,
)
from .utils import (
    send_host_rsvp_notification_email,
    send_rsvp_confirmation_email,
)


class EventViewSet(viewsets.ModelViewSet):
    """
    CRUD for events owned by the authenticated host.

    The queryset is scoped to request.user so a host can never see,
    update, or delete another host's events — attempts return 404.
    """

    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Event.objects.filter(host=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class PublicEventView(APIView):
    """
    GET /api/events/{id}/public/

    Public — returns basic event details for anyone with the link.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PublicEventSerializer(event)
        return Response(serializer.data)


class RSVPCreateView(APIView):
    """
    POST /api/events/{id}/rsvp/

    Public — guests submit an RSVP with no account required.
    Upserts the RSVP record if an RSVP for (event, guest_id) already exists.
    Sends confirmation email to the guest and notification email to the host.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RSVPSerializer(
            data=request.data,
            context={"event": event},
        )
        serializer.is_valid(raise_exception=True)

        guest_id = serializer.validated_data["guest_id"]
        guest_name = serializer.validated_data["guest_name"]
        guest_email = serializer.validated_data["guest_email"]
        rsvp_status = serializer.validated_data["status"]
        plus_one_count = serializer.validated_data.get("plus_one_count", 0)

        rsvp, created = RSVP.objects.update_or_create(
            event=event,
            guest_id=guest_id,
            defaults={
                "guest_name": guest_name,
                "guest_email": guest_email,
                "status": rsvp_status,
                "plus_one_count": plus_one_count,
            },
        )

        email_sent = send_rsvp_confirmation_email(rsvp, event)
        host_notified = send_host_rsvp_notification_email(rsvp, event)

        res_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(
            {
                "message": "RSVP submitted successfully.",
                "guest_name": rsvp.guest_name,
                "guest_email": rsvp.guest_email,
                "status": rsvp.status,
                "plus_one_count": rsvp.plus_one_count,
                "event_title": event.title,
                "email_sent": email_sent,
                "host_notified": host_notified,
            },
            status=res_status,
        )



class RSVPListView(APIView):
    """
    GET /api/events/{id}/rsvps/

    Authenticated — returns the full RSVP list with summary counts,
    but only if the requesting user is the event's host.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        # Scoped to the authenticated host — returns 404 if not the owner
        try:
            event = Event.objects.get(pk=event_id, host=request.user)
        except Event.DoesNotExist:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        rsvps = event.rsvps.all().order_by("-created_at")

        # Build summary counts
        summary = rsvps.aggregate(
            yes_count=Count("id", filter=Q(status="yes")),
            no_count=Count("id", filter=Q(status="no")),
            maybe_count=Count("id", filter=Q(status="maybe")),
            total_plus_ones=Sum("plus_one_count"),
        )
        summary["total_plus_ones"] = summary["total_plus_ones"] or 0
        summary["total_rsvps"] = rsvps.count()

        serializer = RSVPListSerializer(rsvps, many=True)

        return Response(
            {
                "summary": summary,
                "rsvps": serializer.data,
            }
        )
