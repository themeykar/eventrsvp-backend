# EventRSVP — Backend

A Django REST Framework API for EventRSVP: hosts create and manage events, guests RSVP without needing an account.

## What this does

Hosts sign up, log in, and create events they own. Each event gets a public RSVP link that anyone can use — no account needed. Guests submit their name, email, RSVP status (yes/no/maybe), and an optional plus-one count. If a guest resubmits (same event, same guest), their existing RSVP gets updated instead of creating a duplicate.

On a successful RSVP, the guest gets an email confirmation and the host gets notified that a new response came in. Hosts can also export their full guest list as a CSV.

## Tech stack

- Django + Django REST Framework
- SimpleJWT for host authentication
- PostgreSQL (Neon) in production, SQLite locally
- Resend for transactional email

## Setup

1. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your own values (database URL, secret key, Resend API key, etc). Don't commit `.env`.
3. Run migrations:
   ```
   python manage.py migrate
   ```
4. Create a superuser if you want access to Django admin:
   ```
   python manage.py createsuperuser
   ```
5. Run the server:
   ```
   python manage.py runserver
   ```

## API overview

**Auth (host only)**
- `POST /auth/signup/`
- `POST /auth/login/`
- `POST /auth/refresh/`
- `GET /auth/me/`

**Events (host only, JWT required)**
- Full CRUD, scoped to the logged-in host. Trying to access another host's event returns a 404, not a 403 — this is intentional, so hosts can't tell whether an event exists at all if it isn't theirs.

**RSVPs**
- `GET /events/<id>/public/` — public event details, no auth
- `POST /events/<id>/rsvp/` — public, no auth. This is an upsert: submitting again with the same guest identity updates the existing RSVP instead of creating a new one.
- `GET /events/<id>/rsvps/` — host only, returns the full guest list plus summary counts (yes/no/maybe totals)
- `GET /events/<id>/rsvps/export/` — host only, returns the guest list as a downloadable CSV

## How auth and ownership work

Hosts authenticate with JWT (SimpleJWT). Every event and RSVP-management endpoint checks that the requesting host actually owns the event before returning anything — attempting to access an event you don't own behaves identically to that event not existing.

Guests never authenticate. They're identified by an anonymous `guest_id` tied to a specific event, which is what makes the upsert-on-resubmit and guest-side RSVP editing possible without accounts.

## Known limitations

- **Email delivery is limited right now.** This project uses Resend's free tier without a verified custom domain, which means guest confirmation emails and host notification emails only actually deliver to the Resend account owner's verified email address. Everything else in the flow works correctly (the request succeeds, `email_sent` reflects the real outcome), but real inboxes won't receive mail until a custom domain is verified with Resend. This is a deliberate tradeoff for now, not a bug.
- **No scheduled reminder emails.** Would require a cron-style scheduled job (e.g. GitHub Actions), which isn't set up here.
- **No co-hosts.** One host per event, no shared ownership.
- **No custom per-event RSVP questions.** The RSVP form is fixed (name, email, status, plus-one count).
- **No capacity or waitlist logic.** Events don't cap attendance.

These were all deliberately left out of scope rather than overlooked — they're documented here so it's clear what this API does and doesn't try to do.
