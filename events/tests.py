from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Event, RSVP
from .utils import send_host_rsvp_notification_email, send_rsvp_confirmation_email

User = get_user_model()


class HostRSVPNotificationTests(APITestCase):

    def setUp(self):
        self.host = User.objects.create_user(
            username="test_host",
            email="host@example.com",
            password="password123",
            first_name="Jane",
        )
        self.event = Event.objects.create(
            host=self.host,
            title="Tech Conference 2026",
            description="Annual tech conference",
            date_time=timezone.now(),
            location="Main Auditorium",
        )

    @patch("events.utils.config")
    @patch("resend.Emails.send")
    def test_send_host_rsvp_notification_email_success(self, mock_resend_send, mock_config):
        mock_config.side_effect = lambda key, default="": "fake-api-key" if key == "RESEND_API_KEY" else default

        rsvp = RSVP.objects.create(
            event=self.event,
            guest_name="John Doe",
            guest_email="john@example.com",
            status="yes",
            plus_one_count=1,
            guest_id="guest_1",
        )

        result = send_host_rsvp_notification_email(rsvp, self.event)
        self.assertTrue(result)
        mock_resend_send.assert_called_once()

        call_args = mock_resend_send.call_args[0][0]
        self.assertEqual(call_args["to"], ["host@example.com"])
        self.assertIn("Tech Conference 2026", call_args["subject"])
        self.assertIn("John Doe", call_args["html"])

    @patch("events.utils.config")
    def test_send_host_rsvp_notification_email_missing_api_key(self, mock_config):
        mock_config.side_effect = lambda key, default="": "" if key == "RESEND_API_KEY" else default

        rsvp = RSVP.objects.create(
            event=self.event,
            guest_name="John Doe",
            guest_email="john@example.com",
            status="yes",
            plus_one_count=0,
            guest_id="guest_1",
        )

        result = send_host_rsvp_notification_email(rsvp, self.event)
        self.assertFalse(result)

    @patch("events.utils.config")
    @patch("resend.Emails.send")
    def test_send_host_rsvp_notification_email_handles_exception(self, mock_resend_send, mock_config):
        mock_config.side_effect = lambda key, default="": "fake-api-key" if key == "RESEND_API_KEY" else default
        mock_resend_send.side_effect = Exception("Resend API Error")

        rsvp = RSVP.objects.create(
            event=self.event,
            guest_name="John Doe",
            guest_email="john@example.com",
            status="yes",
            plus_one_count=0,
            guest_id="guest_1",
        )

        result = send_host_rsvp_notification_email(rsvp, self.event)
        self.assertFalse(result)

    @patch("events.views.send_host_rsvp_notification_email")
    @patch("events.views.send_rsvp_confirmation_email")
    def test_rsvp_create_view_dual_email_response(self, mock_guest_email, mock_host_email):
        mock_guest_email.return_value = True
        mock_host_email.return_value = True

        url = f"/api/events/{self.event.id}/rsvp/"
        data = {
            "guest_id": "guest_abc",
            "guest_name": "Alice Wonderland",
            "guest_email": "alice@example.com",
            "status": "yes",
            "plus_one_count": 2,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email_sent"], True)
        self.assertEqual(response.data["host_notified"], True)

        mock_guest_email.assert_called_once()
        mock_host_email.assert_called_once()

    @patch("events.views.send_host_rsvp_notification_email")
    @patch("events.views.send_rsvp_confirmation_email")
    def test_rsvp_create_view_independent_email_failures(self, mock_guest_email, mock_host_email):
        # Guest email fails, Host email succeeds
        mock_guest_email.return_value = False
        mock_host_email.return_value = True

        url = f"/api/events/{self.event.id}/rsvp/"
        data = {
            "guest_id": "guest_abc",
            "guest_name": "Bob Builder",
            "guest_email": "bob@example.com",
            "status": "maybe",
            "plus_one_count": 0,
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email_sent"], False)
        self.assertEqual(response.data["host_notified"], True)

        # Verify database record updated
        rsvp = RSVP.objects.get(event=self.event, guest_id="guest_abc")
        self.assertEqual(rsvp.guest_name, "Bob Builder")

