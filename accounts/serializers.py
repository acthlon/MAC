from django.core.exceptions import ValidationError
from rest_framework import serializers

from accounts.models import CustomUser
from accounts.utils.passwordvalidate import validate_password_strength
from core.constants import MAX_FILE_SIZE


class CustomUserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length= 9)
    confirm_password = serializers.CharField(write_only=True,min_length=9)
    username= serializers.CharField(read_only=True)


    def validate(self,data):

        request_method = self.context['request'].method

        if request_method == 'POST':
            
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            
            if password != confirm_password:
                raise ValidationError('The passwords must match')
            
            if password:
                if not validate_password_strength(password):
                    raise serializers.ValidationError("Password doesn't meet the requirements")
        return data        


    def create(self,validated_data):
        validated_data.pop('confirm_password',None) # we removed confirm_password because we don't need it for creating the user we only needed to validate password
        # password = validated_data.pop("password")
        user = CustomUser.objects.create_user(**validated_data)
        # user.set_password(password)  i don't need this anymore, create_user function will create the user and hash the password automatically and save too 
        # user.save()
        return user
    
   
    class Meta:
        model = CustomUser
        fields = ("password","confirm_password","email","phone","first_name","last_name","username","gender")
        

class UserProfileSerializer(serializers.ModelSerializer):
            
    class Meta:
        model = CustomUser
        
        fields = ['country', 'state', 'city', 'address','profile_image','phone','gender','email','first_name','last_name']       
        read_only_fields = ['gender','email','first_name','last_name'] 


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    
    
    def validate(self,data):

        request = self.context['request']
        request_method = request.method
        user = request.user  


        if request_method == 'PATCH':
                        
            if 'profile_image' in data:
                profile_image = data.get('profile_image')

                if profile_image and profile_image.size > MAX_FILE_SIZE:
                    raise serializers.ValidationError({'message': 'Profile Image must not exceed 5MB'})
        return data
     
            
    class Meta:
        model = CustomUser
        fields = ['country', 'state', 'city', 'address','profile_image','username']        



class UpdatePasswordSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(required=True)
    old_password = serializers.CharField(write_only = True, required=True)
    confirm_password = serializers.CharField(write_only = True,required=True)
    
    
    def validate(self,data):
        
        request = self.context.get('request')
        user = request.user
        
        # since requred =True already then these lnes are not needed anymore
        # if 'old_password' not in data:
        #     raise serializers.ValidationError({'password':'old_password is required'})

        # if 'password' not in data:
        #     raise serializers.ValidationError({'password':'password is required'})

        # if 'confirm_password' not in data:
        #     raise serializers.ValidationError({'password':'confirm_password is required'})
        # if 'password' in data and 'confirm_password' in data and 'old_password' in data:
        
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        old_password = data.get('old_password')
        
        if old_password and not user.check_password(old_password):

            raise serializers.ValidationError({'message': "Old password doesn't match"})
            
        if password != confirm_password:
            raise ValidationError('The passwords must match')
        
        if not validate_password_strength(password):
            raise serializers.ValidationError({'message': "Password doesn't meet the requirements"})
        return data
                
                
    def update(self,instance,validated_data):

        password = validated_data.get('password')
        instance.set_password(password)
        instance.save()
        return {"message": "Password updated successfully"}
         
    class Meta:
        model = CustomUser
        fields = ['password','old_password','confirm_password']