from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.models import Payment
from notifications.tasks import send_welcome_email_task,send_order_confirmation_email_task,send_order_status_update_email_task,send_refund_confirmation_email
from accounts.models import CustomUser
from order.models import Order
from payments.models import RefundRequest



@receiver(post_save,sender=CustomUser)
def welcome_email_handler(sender,instance,created,**kwargs):
    
    if instance.is_active and not instance.last_login:
        send_welcome_email_task.delay(instance.id)




@receiver(post_save,sender=Order)
def order_confirmation_status_handler(sender,instance,created,**kwargs):
    
    if instance.status == 'CONFIRMED' and not instance.tracking_id:
        send_order_confirmation_email_task.delay(instance.id,instance.user.id)
    
            


@receiver(post_save,sender=Order)
def order_status_change_handler(sender,instance,created,**kwargs):
    
    if instance.status != 'CREATED' and instance.tracking_id:
        send_order_status_update_email_task.delay(instance.id,instance.status,instance.user.id)
        


@receiver(post_save,sender=RefundRequest)
def refund_confrmation_handler(sender,instance,created,**kwargs):
    
    if instance.status != 'PENDING':
        send_refund_confirmation_email.delay(instance.id,instance.user.id)
        print('THIS WAS DONE SUCCESSFULLY')