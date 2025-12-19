from rest_framework import serializers
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField
from accounts.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only = True)
    phone = PhoneNumberField()


    def create(self,validated_data):
        password = validated_data.pop("password")
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save
        return user
    
    class Meta:
        model = get_user_model()
        fields = ("password","username","email","phone","country","state","city")
        
