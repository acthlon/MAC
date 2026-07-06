from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.deconstruct import deconstructible
import uuid
from django.contrib.auth.models import BaseUserManager


@deconstructible
class generated_image_path():

    def __init__(self):
        pass

    def __call__(self,instance,filename):

        extension = filename.split('.')[-1]
        path = f'images/profile/{instance.user.username}.{extension}'
        return path

image_path = generated_image_path()    





class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)



class CustomUser(AbstractUser):
 
    MALE = "Male"
    FEMALE = "Female"
    OTHERS = "Others"

    GENDER_CATEGORY = [
        (MALE,"Male"),
        (FEMALE,"Female"),
        (OTHERS,"Others")
    ] 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = PhoneNumberField()
    is_active= models.BooleanField(default=False)
    gender = models.CharField(choices=GENDER_CATEGORY)
    email = models.EmailField(max_length = 500,unique=True)
    
    # Profile fields
    
    country = models.CharField(max_length = 500, null=True, blank=True)
    state = models.CharField(max_length = 200, null=True, blank=True)
    city = models.CharField(max_length=500, null=True, blank=True)
    address = models.TextField(max_length = 1000, null=True, blank=True)
    profile_image = models.ImageField(upload_to=image_path, null = True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()


    def phone_number(self):
        return str(self.phone)
    

    class Meta:
        verbose_name_plural = 'Users'    
        ordering = ['-created_at']    

    def __str__(self):
        return f"{self.username}"