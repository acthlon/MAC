from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

class CustomUser(AbstractUser):

    country = models.CharField(max_length = 500, null=True, blank=True)
    state = models.CharField(max_length = 200)
    city = models.CharField(max_length=500)
    address = models.TextField(max_length = 1000)
    email = models.EmailField(max_length = 500, null=True, blank=True,unique=True)
    phone = PhoneNumberField(null=True,blank=True)
    

    def __str__(self):
        return f"{self.username}"

