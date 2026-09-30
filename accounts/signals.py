from functools import partial
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models import CustomUser
from accounts.tasks import send_welcome_email_task


@receiver(pre_save, sender=CustomUser)
def create_username(sender, instance, **kwargs):

    first_name = instance.first_name
    last_name = instance.last_name

    if not instance.username:
        username = instance.email.split("@")[0]

        instance.username = username


@receiver(post_save, sender=CustomUser)
def welcome_email_handler(sender, instance, created, **kwargs):

    if instance.is_active and not instance.last_login:
        transaction.on_commit(partial(send_welcome_email_task.delay, instance.id))
