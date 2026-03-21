from django.db.models.signals import pre_save,post_save
from accounts.models import CustomUser,UserProfile
from django.dispatch import receiver

@receiver(pre_save,sender=CustomUser)
def create_username(sender,instance,**kwargs):

    first_name = instance.first_name
    last_name = instance.last_name

    if not instance.username:
        username = f"{first_name}-{last_name}".lower().title()

        instance.username = username

@receiver(post_save,sender=CustomUser)
def create_user_profile(sender,instance,created,**kwargs):
    
    if created:
        UserProfile.objects.create(user=instance)   

# @receiver(post_save,sender=CustomUser)
# def update_user_profile(sender,instance,**kwargs):

#     instance.userprofile.save()
