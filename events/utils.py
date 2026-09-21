import logging
from decouple import config
import resend

logger = logging.getLogger(__name__)


def send_rsvp_confirmation_email(rsvp, event):
    """
    Sends an RSVP confirmation email using Resend.
    Returns True if sent successfully, False if failed.
    Does not raise exceptions on email failure.
    """
    api_key = config("RESEND_API_KEY", default="")
    if not api_key:
        logger.warning("RESEND_API_KEY is not set. Skipping confirmation email.")
        return False

    resend.api_key = api_key

    # Subject and status title based on RSVP status
    status_display = rsvp.get_status_display()
    if rsvp.status == "yes":
        subject = f"You're confirmed for {event.title}!"
    elif rsvp.status == "no":
        subject = f"RSVP Received: {event.title}"
    else:
        subject = f"RSVP Update: {event.title}"

    date_str = (
        event.date_time.strftime("%B %d, %Y at %I:%M %p")
        if hasattr(event.date_time, "strftime")
        else str(event.date_time)
    )

    plus_one_html = ""
    if rsvp.plus_one_count > 0:
        plus_one_html = f"<p style='margin: 4px 0; color: #4b5563;'><strong>Plus Ones:</strong> {rsvp.plus_one_count}</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{subject}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px;">
      <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e5e7eb;">
        <div style="background-color: #4f46e5; padding: 24px; text-align: center;">
          <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 600;">{event.title}</h1>
        </div>
        <div style="padding: 24px; color: #1f2937;">
          <p style="font-size: 16px; margin-top: 0;">Hi <strong>{rsvp.guest_name}</strong>,</p>
          <p style="font-size: 14px; color: #4b5563;">Your RSVP response has been received:</p>
          
          <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px; margin: 16px 0;">
            <p style="margin: 4px 0; color: #4b5563;"><strong>Status:</strong> {status_display}</p>
            {plus_one_html}
            <p style="margin: 4px 0; color: #4b5563;"><strong>When:</strong> {date_str}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Where:</strong> {event.location}</p>
            {f'<p style="margin: 4px 0; color: #4b5563;"><strong>Details:</strong> {event.description}</p>' if event.description else ''}
          </div>
          
          <p style="font-size: 12px; color: #9ca3af; margin-bottom: 0; text-align: center;">
            Sent via EventRSVP
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from": "updates.eventrsvp.site",
            "to": [rsvp.guest_email],
            "subject": subject,
            "html": html_content,
        })
        return True
    except Exception as e:
        logger.error(f"Error sending confirmation email to {rsvp.guest_email}: {e}")
        return False


def send_host_rsvp_notification_email(rsvp, event):
    """
    Sends an RSVP notification email to the event host using Resend.
    Returns True if sent successfully, False if failed.
    Does not raise exceptions on email failure.
    """
    api_key = config("RESEND_API_KEY", default="")
    if not api_key:
        logger.warning("RESEND_API_KEY is not set. Skipping host notification email.")
        return False

    host_email = getattr(getattr(event, "host", None), "email", None)
    if not host_email:
        logger.warning(f"Event {event.id} host email is not available. Skipping host notification.")
        return False

    resend.api_key = api_key

    subject = f"New RSVP for {event.title}"
    status_display = rsvp.get_status_display()

    plus_one_html = ""
    if rsvp.plus_one_count > 0:
        plus_one_html = f"<p style='margin: 4px 0; color: #4b5563;'><strong>Plus Ones:</strong> {rsvp.plus_one_count}</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{subject}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px;">
      <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e5e7eb;">
        <div style="background-color: #4f46e5; padding: 24px; text-align: center;">
          <h1 style="color: #ffffff; margin: 0; font-size: 20px; font-weight: 600;">{subject}</h1>
        </div>
        <div style="padding: 24px; color: #1f2937;">
          <p style="font-size: 16px; margin-top: 0;">Hi <strong>{event.host.first_name or event.host.username}</strong>,</p>
          <p style="font-size: 14px; color: #4b5563;">A guest has submitted an RSVP for your event <strong>{event.title}</strong>:</p>
          
          <div style="background-color: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px; margin: 16px 0;">
            <p style="margin: 4px 0; color: #4b5563;"><strong>Guest Name:</strong> {rsvp.guest_name}</p>
            <p style="margin: 4px 0; color: #4b5563;"><strong>Status:</strong> {status_display}</p>
            {plus_one_html}
          </div>

          <p style="font-size: 14px; color: #4b5563;">
            Log in to your dashboard to see the full list of RSVPs for your event.
          </p>
          
          <p style="font-size: 12px; color: #9ca3af; margin-bottom: 0; text-align: center;">
            Sent via EventRSVP
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": [host_email],
            "subject": subject,
            "html": html_content,
        })
        return True
    except Exception as e:
        logger.error(f"Error sending host notification email to {host_email}: {e}")
        return False

