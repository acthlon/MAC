from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.models import Payment
from notifications.tasks import send_welcome_email_task,send_order_confirmation_email_task,send_order_status_update_email_task
from accounts.models import CustomUser
from order.models import Order



@receiver(post_save,sender=CustomUser)
def welcome_email_handler(sender,instance,created,**kwargs):
    
    if instance.is_active:
        send_welcome_email_task(instance.id)


@receiver(post_save,sender=Payment)
def payment_status_handler(sender,instance,created,**kwargs):
    
    if instance.status == 'SUCCESSFUL':
        print('this is it')
        send_order_confirmation_email_task(instance.order,instance.user.id)


@receiver(post_save,sender=Order)
def order_status_change_handler(sender,instance,created,**kwargs):
    
    if instance.status != 'CREATED':
        send_order_status_update_email_task(instance,instance.status,instance.user.id)