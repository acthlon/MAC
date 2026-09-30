from functools import partial

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.choices import ReturnStatus
from payments.models import ReturnRequest
from payments.tasks import send_refund_confirmation_email


@receiver(post_save, sender=ReturnRequest)
def refund_confrmation_handler(sender, instance, created, **kwargs):

    if instance.status in [
        ReturnStatus.APPROVED,
        ReturnStatus.REJECTED,
        ReturnStatus.COMPLETED,
        ReturnStatus.UNDER_REVIEW,
    ]:
        transaction.on_commit(
            partial(send_refund_confirmation_email.delay, instance.id, instance.user.id)
        )
