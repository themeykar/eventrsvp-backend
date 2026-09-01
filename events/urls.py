from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("", views.EventViewSet, basename="event")

urlpatterns = [
    # Public endpoints (no auth required)
    path("<int:event_id>/public/", views.PublicEventView.as_view(), name="event-public"),
    path("<int:event_id>/rsvp/", views.RSVPCreateView.as_view(), name="rsvp-create"),

    # Authenticated endpoints (host-only, JWT required)
    path("<int:event_id>/rsvps/", views.RSVPListView.as_view(), name="rsvp-list"),
    path("<int:event_id>/rsvps/export/", views.RSVPExportView.as_view(), name="rsvp-export"),

    # Router-generated CRUD routes (must come last to avoid conflicts)
    path("", include(router.urls)),
]
