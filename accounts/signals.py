from django.db.models.signals import pre_save,post_save
from accounts.models import CustomUser
from django.dispatch import receiver
from accounts.tasks import send_welcome_email_task







@receiver(pre_save,sender=CustomUser)
def create_username(sender,instance,**kwargs):

    first_name = instance.first_name
    last_name = instance.last_name

    if not instance.username:
        username = f"{first_name}-{last_name}".lower().title()

        instance.username = username


@receiver(post_save,sender=CustomUser)
def welcome_email_handler(sender,instance,created,**kwargs):
    
    if instance.is_active and not instance.last_login:
        send_welcome_email_task.delay(instance.id)



# @receiver(post_save,sender=CustomUser)
# def update_user_profile(sender,instance,**kwargs):

#     instance.userprofile.save()
