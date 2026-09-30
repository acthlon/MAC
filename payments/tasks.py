from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from paystackapi.refund import Refund

from accounts.models import CustomUser
from core.choices import ReturnStatus
from order.models import Order
from payments.models import ReturnRequest


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_refund_confirmation_email(self, refund_id, user_id):

    try:
        refund_request = ReturnRequest.objects.get(id=refund_id, user__id=user_id)
        site_url = settings.SITE_URL

        subject = f"Refund Processed Successfully - Order #{refund_request.order.id}"

        context = {
            "user": refund_request.user,
            "order": refund_request.order,
            "reason": refund_request.reason,
            "return_amount": refund_request.return_amount,
            "processed_at": refund_request.processed_at,
            "site_url": site_url,
        }

        if refund_request.status == ReturnStatus.UNDER_REVIEW:
            html_message = render_to_string(
                "email/refund/refund-review.html", context=context
            )

        elif refund_request.status == ReturnStatus.APPROVED:
            html_message = render_to_string(
                "email/refund/refund-approved.html", context=context
            )

        elif refund_request.status == ReturnStatus.REJECTED:
            html_message = render_to_string(
                "email/refund/refund-rejected.html", context=context
            )

        elif refund_request.status == ReturnStatus.PROCESSING:
            html_message = render_to_string(
                "email/refund/refund-processing.html", context=context
            )

        elif refund_request.status == ReturnStatus.COMPLETED:
            html_message = render_to_string(
                "email/refund/refund-completed.html", context=context
            )
        else:
            return {
                "status": "skipped",
                "reason": f"Unexpected status: {refund_request.status}",
            }

        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[refund_request.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return True

    except Exception as e:
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_paystack_return(self, return_id, user_id):

    # Step 1: Lock the row and check if already processed
    with transaction.atomic():
        return_request = ReturnRequest.objects.select_for_update().get(
            id=return_id, user_id=user_id
        )

        if return_request.status in [ReturnStatus.PROCESSING, ReturnStatus.COMPLETED]:
            return {
                "status": "skipped",
                "reason": "This return request has already been processed.",
            }

        # Grab what we need while inside the lock
        order = return_request.order
        order_item = return_request.order_item if return_request.order_item else None

    # Step 2: Call Paystack API (outside the lock — never hold a DB lock during a network call)
    return_amount = (
        return_request.return_amount
        if return_request.return_amount is not None
        else (order_item.total_amount if order_item else order.total_amount)
    )
    amount_in_kobo = int(return_amount * 100)

    return_api = Refund(secret_key=settings.PAYSTACK_SECRET_KEY)

    response = return_api.create(
        transaction=order.payment_reference,
        amount=amount_in_kobo,
        reason=return_request.reason,
    )

    success = response.get("status", False)
    message = response.get("message", "No message")

    if success:
        # Step 3: Paystack succeeded — restore stock and update status
        with transaction.atomic():
            if order and not order_item:
                for item in order.items.all():
                    item_obj = item.content_object
                    if item_obj and hasattr(item_obj, "stock"):
                        item_obj.stock += item.quantity
                        item_obj.save()

            elif order_item:
                item_obj = order_item.content_object
                if item_obj and hasattr(item_obj, "stock"):
                    item_obj.stock += order_item.quantity
                    item_obj.save()

            return_request.status = ReturnStatus.PROCESSING
            return_request.processed_at = timezone.now()
            return_request.save()

            return True

    else:
        # Step 4: Paystack failed — retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (self.request.retries + 1)
            raise self.retry(exc=Exception(message), countdown=countdown)

        # ALL 3 RETRIES EXHAUSTED: Record failure details in DB
        return_request.rejection_reason = (
            f"Automatic Paystack refund failed after 3 attempts: {message}"
        )
        return_request.save()
        return False


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_admin_stock_shortage_alert_task(self, order_id):
    try:
        order = (
            Order.objects.select_related("user")
            .prefetch_related("items")
            .get(id=order_id)
        )
        subject = f"🚨 Marvelam Alert: Stock Shortage for Order #{order.order_number}"

        context = {
            "order": order,
            "user": order.user,
            "orderitems": order.items.all(),
            "admin_notes": order.admin_notes,
            "site_url": getattr(settings, "SITE_URL", ""),
            "website_url": getattr(settings, "SITE_URL", ""),
        }

        html_message = render_to_string(
            "email/admin/stock-shortage-alert.html",
            context=context,
        )
        plain_message = strip_tags(html_message)

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

    except Exception as exc:
        raise self.retry(exc=exc)
