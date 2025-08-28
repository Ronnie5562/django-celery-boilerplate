from django.conf import settings
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator

from users.tokens import generate_token
from users.tasks import send_email_task


def generate_email_message(user):
    name = user.first_name or user.last_name or user.email.split("@")[0]
    return f"""
Hi {name},

Welcome to our Platform! Your account is set up, and you're almost ready. Please verify your email to gain access.

For any assistance, feel free to reach out. We're here to support you.

The Platform Team
"""


class EmailService:
    def send_welcome_email(self, user):
        subject = "Welcome Email"
        message = generate_email_message(user)
        send_email_task.delay(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            content_subtype="plain"
        )

    def send_account_verification_email(self, request, user):
        current_site = get_current_site(request)
        subject = "Verify Your Email"
        name = user.first_name or user.last_name or user.email.split('@')[0]

        body = render_to_string(
            "mail/email_confirmation.html",
            {
                "name": name,
                "domain": current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": generate_token.make_token(user),
            },
        )
        send_email_task.delay(
            subject,
            body,
            settings.EMAIL_HOST_USER,
            [user.email],
            content_subtype="html"
        )

    def send_password_reset_link(self, request, user):
        current_site = get_current_site(request)
        subject = "Password Reset Request - Platform"
        name = user.first_name or user.last_name or user.email.split('@')[0]

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        protocol = 'https' if request.is_secure() else 'http'
        reset_link = f"{protocol}://{current_site.domain}/users/password-reset-confirm/{uidb64}/{token}/"

        try:
            body = render_to_string(
                "mail/password_reset.html",
                {
                    "name": name,
                    "reset_link": reset_link,
                    "domain": current_site.domain,
                    "protocol": protocol,
                    "user": user,
                }
            )
            subtype = "html"
        except Exception:
            body = f"""
Hi {name},

You requested a password reset. Click below to set a new password:
{reset_link}

This link will expire in 24 hours.
"""
            subtype = "plain"

        send_email_task.delay(
            subject,
            body,
            settings.EMAIL_HOST_USER,
            [user.email],
            content_subtype=subtype
        )

    def send_password_reset_confirmation(self, user):
        subject = "Password Reset Successful - Platform"
        name = user.first_name or user.last_name or user.email.split('@')[0]

        try:
            body = render_to_string(
                "mail/password_reset_confirmation.html", {"name": name, "user": user})
            subtype = "html"
        except Exception:
            body = f"""
Hi {name},

Your password has been reset successfully.

If this wasn't you, contact support at {settings.EMAIL_HOST_USER}.
"""
            subtype = "plain"

        send_email_task.delay(
            subject,
            body,
            settings.EMAIL_HOST_USER,
            [user.email],
            content_subtype=subtype
        )
