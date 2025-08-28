from celery import shared_task
from django.core.mail import EmailMessage


@shared_task(bind=True, max_retries=3)
def send_email_task(
    self, subject, body, from_email, recipient_list, content_subtype="plain"
):
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=recipient_list,
        )
        if content_subtype == "html":
            email.content_subtype = "html"
        email.send(fail_silently=False)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)  # retry after 1 min
