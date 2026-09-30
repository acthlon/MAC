from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from accounts.models import CustomUser
from core.choices import DeliveryStatus, OrderStatus
from order.models import Order


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email_task(self, order_id, user_id):

    user = CustomUser.objects.get(id=user_id)

    order = Order.objects.get(id=order_id, user=user)

    try:
        subject = f"Order Confirmation - #{order.order_number}"
        context = {
            "order": order,
            "user": user,
            "orderitems": order.items.all(),
            "website_url": getattr(settings, "SITE_URL", ""),
        }

        if order.status == OrderStatus.CONFIRMED:
            html_message = render_to_string("email/order/order-confirm.html", context)
        elif order.status == OrderStatus.FAILED:
            html_message = render_to_string("email/order/order-failed.html", context)
        else:
            return {"status": "skipped", "reason": f"Unexpected status: {order.status}"}

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
def send_admin_order_confirmation_email_task(self, order_id):
    try:
        order = (
            Order.objects.select_related("user")
            .prefetch_related("items")
            .get(id=order_id)
        )
        subject = f"🔔 New Order Received - #{order.order_number}"

        context = {
            "order": order,
            "user": order.user,
            "orderitems": order.items.all(),
            "site_url": getattr(settings, "SITE_URL", ""),
            "website_url": getattr(settings, "SITE_URL", ""),
        }

        # Uses your existing new-order template for admins
        html_message = render_to_string("email/admin/new-order.html", context=context)
        plain_message = strip_tags(html_message)

        # Query all active staff emails
        staff_emails = list(
            CustomUser.objects.filter(is_staff=True, is_active=True)
            .exclude(email__isnull=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )

        recipient_list = (
            staff_emails
            if staff_emails
            else [admin[1] for admin in getattr(settings, "ADMINS", [])]
            or [settings.DEFAULT_FROM_EMAIL]
        )

        for email in recipient_list:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
        return {"status": "sent", "order": order.order_number, "status_code": 200}

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_update_email_task(self, order_id, new_status, user_id):

    try:
        order = Order.objects.get(id=order_id)
        user = order.user
        subject = f"Order Update - #{order.order_number} - {new_status}"
        website_url = settings.SITE_URL

        context = {
            "order": order,
            "status": new_status,
            "user": user,
            "website_url": website_url,
            "orderitems": order.items.all(),
        }

        if order.delivery_status == DeliveryStatus.WAITING_TO_BE_SHIPPED:
            html_message = render_to_string(
                "email/order/order-processing.html", context
            )

        elif order.delivery_status == DeliveryStatus.SHIPPED:
            html_message = render_to_string("email/order/order-shipped.html", context)

        elif order.delivery_status == DeliveryStatus.OUT_FOR_DELIVERY:
            html_message = render_to_string(
                "email/order/out-for-delivery.html", context
            )

        elif order.delivery_status == DeliveryStatus.DELIVERED:
            html_message = render_to_string("email/order/order-delivered.html", context)

        elif order.delivery_status == DeliveryStatus.FAILED_DELIVERY:
            html_message = render_to_string(
                "email/order/order-failed-delivery.html", context
            )

        elif order.delivery_status == DeliveryStatus.CANCELED:
            html_message = render_to_string("email/order/order-canceled.html", context)

        elif order.delivery_status == DeliveryStatus.RETURNED:
            html_message = render_to_string("email/order/order-returned.html", context)

        else:
            return {
                "status": "skipped",
                "reason": f"Unexpected delivery status: {order.delivery_status}",
            }

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
