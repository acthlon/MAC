from django.db.models.signals import post_save
from django.dispatch import receiver

from order.models import Order
from order.tasks import (
    send_order_confirmation_email_task,
    send_order_status_update_email_task,
)


@receiver(post_save, sender=Order)
def order_confirmation_status_handler(sender, instance, created, **kwargs):

    if instance.status in ["CONFIRMED", "FAILED"] and not instance.tracking_id:
        send_order_confirmation_email_task.delay(instance.id, instance.user.id)


@receiver(post_save, sender=Order)
def order_status_change_handler(sender, instance, created, **kwargs):

    if (
        instance.status in ["SHIPPED", "COMPLETED", "CANCELED", "RETURNED"]
        and instance.tracking_id
    ):
        send_order_status_update_email_task.delay(
            instance.id, instance.status, instance.user.id
        )
