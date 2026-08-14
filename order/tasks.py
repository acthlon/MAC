from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags

from order.models import Order


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email_task(self, order_id, user_id):

    order = Order.objects.get(id=order_id)
    user = order.user

    try:
        subject = f"Order Confirmation - #{order.id}"
        context = {"order": order, "user": user, "orderitems": order.orderitems.all()}

        if order.status == "CONFIRMED":
            html_message = render_to_string("email/order-confirm.html", context)
        elif order.status == "FAILED":
            html_message = render_to_string("email/order-failed.html", context)

        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "sent", "email": user.email, "status_code": 200}

    except Exception as e:
        print(f"Error sending confirmation email: {e!s}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_update_email_task(self, order_id, new_status, user_id):

    try:
        order = Order.objects.get(id=order_id)
        user = order.user
        subject = f"Order Update - #{order.id} - {new_status}"
        site_domain = settings.SITE_URL
        home_url = reverse()
        website_url = f"{site_domain}{home_url}"

        context = {
            "order": order,
            "status": new_status,
            "user": user,
            "website_url": website_url,
        }

        if order.status == "SHIPPED":
            html_message = render_to_string("email/order/order-shipped.html", context)

        elif order.status == "COMPLETED":
            html_message = render_to_string("email/order/order-completed.html", context)

        elif order.status == "CANCELED":
            html_message = render_to_string("email/order/order-cancelled.html", context)

        elif order.status == "RETURNED":
            html_message = render_to_string("email/order/order-returned.html", context)

        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "sent", "email": user.email, "status_code": 200}

    except Exception as e:
        raise self.retry(exc=e)
