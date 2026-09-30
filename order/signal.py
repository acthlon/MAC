from functools import partial

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.choices import DeliveryStatus, OrderStatus
from order.models import Order
from order.tasks import (
    send_admin_order_confirmation_email_task,
    send_order_confirmation_email_task,
    send_order_status_update_email_task,
)


@receiver(post_save, sender=Order)
def order_confirmation_status_handler(sender, instance, created, **kwargs):

    status_changed = instance.status != getattr(instance, "_original_status", None)
    delivery_changed = instance.delivery_status != getattr(
        instance, "_original_delivery_status", None
    )

    if (created or status_changed) and instance.status in [
        OrderStatus.CONFIRMED,
        OrderStatus.FAILED,
    ]:
        transaction.on_commit(
            partial(
                send_order_confirmation_email_task.delay,
                instance.id,
                instance.user.id,
            )
        )

    if (created or status_changed) and instance.status == OrderStatus.CONFIRMED:
        transaction.on_commit(
            partial(
                send_admin_order_confirmation_email_task.delay,
                instance.id,
            )
        )

    if (created or delivery_changed) and (
        instance.delivery_status
        in [
            DeliveryStatus.WAITING_TO_BE_SHIPPED,
            DeliveryStatus.SHIPPED,
            DeliveryStatus.OUT_FOR_DELIVERY,
            DeliveryStatus.DELIVERED,
            DeliveryStatus.CANCELED,
            DeliveryStatus.RETURNED,
            DeliveryStatus.FAILED_DELIVERY,
        ]
        and instance.tracking_id
    ):
        transaction.on_commit(
            partial(
                send_order_status_update_email_task.delay,
                instance.id,
                instance.delivery_status,
                instance.user.id,
            )
        )
