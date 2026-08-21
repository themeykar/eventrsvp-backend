from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Event
from .serializers import EventSerializer


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
