import threading
from django.conf import settings
from users.tokens import generate_token
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        # super().__init__(self)
        threading.Thread.__init__(self)

    def run(self):
        self.email.send(fail_silently=True)


def generate_email_message(user):
    name = None
    if user.first_name:
        name = user.first_name
    elif user.last_name:
        name = user.last_name
    else:
        # Extract the part before the "@" in the email
        name = user.email.split("@")[0]

    return f"""
Hi {name},

Welcome to our Platform! Your account is set up, and you're almost all setup. Please verify your email to gain access to the platform.

For any assistance, feel free to reach out. We're here to support you.

Best,
The Platform Team
"""


class EmailService:
    def send_welcome_email(self, user):
        subject = "Welcome Email"
        message = generate_email_message(user)
        welcome_email = EmailMessage(
            subject, message, settings.EMAIL_HOST_USER, [user.email]
        )
        EmailThread(welcome_email).start()

    def send_account_verification_email(self, request, user):
        current_site = get_current_site(request)
        email_confirmation_subject = "Verify Your Email"
        email_confirmation_message = render_to_string(
            "mail/email_confirmation.html",
            {
                "name": user.email.split("@")[0],
                "domain": current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": generate_token.make_token(user),
            },
        )

        email = EmailMessage(
            email_confirmation_subject,
            email_confirmation_message,
            settings.EMAIL_HOST_USER,
            [user.email],
        )
        EmailThread(email).start()
