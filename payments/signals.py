from django.db.models.signals import post_save
from django.dispatch import receiver
from payments.tasks import send_refund_confirmation_email
from payments.models import RefundRequest


        


@receiver(post_save,sender=RefundRequest)
def refund_confrmation_handler(sender,instance,created,**kwargs):
    
    if instance.status != 'PENDING':
        send_refund_confirmation_email.delay(instance.id,instance.user.id)
        print('THIS WAS DONE SUCCESSFULLY')