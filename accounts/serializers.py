from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField as SerializerPhoneNumberField
from accounts.models import CustomUser,UserProfile
from accounts.utils.passwordvalidate import validate_password_strength
from django.core.exceptions import ValidationError
from phonenumbers import PhoneNumber
from django.db import transaction

from accounts.constants import MAX_FILE_SIZE


class CustomUserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=9)
    username= serializers.CharField(read_only=True)


    def validate(self,data):

        request_method = self.context['request'].method

        if request_method == 'POST':

            if 'confirm_password' in data:

                password = data.get('password')
                confirm_password = data.get('confirm_password')
                
                if password != confirm_password:
                    raise ValidationError('The passwords must match')
                validate_password_strength(password)
            

            if 'password' in data:
                password = data.get('password')

                if not validate_password_strength(password):
                    raise serializers.ValidationError("Password doesn't meet the requirements")
        return data        


    @transaction.atomic
    def create(self,validated_data):
        password = validated_data.pop("password")
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
   
    class Meta:
        model = CustomUser
        fields = ("password","email","phone","first_name","last_name","username","gender")
        



class UserProfileSerializer(serializers.ModelSerializer):


    user = CustomUserSerializer(required=False)

    def get_phone(self,obj):
        return obj.get_phone_number()    
    
            
    class Meta:
        model = UserProfile
        
        fields = ['country', 'state', 'city', 'address','profile_image','first_name', 'last_name']        


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    gender = serializers.CharField(required=False)

    class Meta:
        model = CustomUser
        fields = ['country', 'state', 'city', 'address','profile_image', "phone_number", "first_name", "last_name", "email", "username", "gender"]
        read_only_fields = ["email"]        

    
    def validate(self,data):
        user = self.context["request"].user     
        profile_image = data.get('profile_image') 
        username = data.get("username")

        if profile_image and profile_image.size > MAX_FILE_SIZE:
            raise serializers.ValidationError({'message': f'Profile Image must not exceed {MAX_FILE_SIZE}MB'})

        if username and CustomUser.objects.filter(username=username).exclude(id=user.id).first():
            raise serializers.ValidationError({"message": "username exists"})        

        return data
       




class UpdatePasswordSerializer(serializers.Serializer):
    
    password = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    
    def validate(self,data):
        request = self.context.get('request')
        user = request.user
        
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        old_password = data.get('old_password')
        
        if not user.check_password(old_password):
            raise serializers.ValidationError({'message': "Old password doesn't match"})
            
        if password != confirm_password:
            raise ValidationError('The passwords must match')
        
        validate_password_strength(password)
        return data
                
                
    def update(self,instance, validated_data):
        password = validated_data.pop('password')
        instance.set_password(password)
        instance.save(update_fields=["password"])

        return {"message": "Password updated successfully"}
    