from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField as SerializerPhoneNumberField
from accounts.models import CustomUser,UserProfile
from accounts.utils.passwordvalidate import validate_password_strength
from django.core.exceptions import ValidationError
from phonenumbers import PhoneNumber



class CustomUserSerializer(serializers.ModelSerializer):


    password = serializers.CharField(write_only=True, min_length= 9)
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


    user = CustomUserSerializer()

    def get_phone(self,obj):
        return obj.get_phone_number()    
    
            
    class Meta:
        model = UserProfile
        
        fields = ['country', 'state', 'city', 'address','profile_image','user']        


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    
    
    def validate(self,data):

        request = self.context['request']
        request_method = request.method
        user = request.user  


        if request_method in ['PUT','PATCH']:
                        
            if 'profile_image' in data:
                profile_image = data.get('profile_image')

                if profile_image and profile_image.size > 5 * 1024 * 1024:
                    raise serializers.ValidationError({'profile_image': 'Profile Image must not exceed 5MB'})
                

            # if 'first_name' in data:
            #     first_name = data.get('first_name')

            #     if not first_name.isalpha():
            #         raise serializers.ValidationError({'First Name': 'First name should contain only alphabet'})
                

            # if 'phone' in data:
            #     phone = data.get('phone')
            #     try:
            #         phonenumber = PhoneNumber.from_string(phone)

            #         if not phonenumber.is_valid():
                        # raise serializers.ValidationError('Phone number is not valid')     
                # except Exception as e:
                    # raise serializers.ValidationError({'phone':str(e)})


            # if 'last_name' in data:
            #     last_name = data.get('last_name')

            #     if not last_name.isalpha():
            #         raise serializers.ValidationError({'Last Name': 'Last name should contain only alphabet'})
                    

            # if 'email' in data:
            #     new_email = data.get('email')
            #     if CustomUser.objects.filter(email=new_email).exclude(id=user.id).exists():
            #         raise serializers.ValidationError({'email':'Email is already in use by another user'})
        return data
     
     
    def update(self,instance,validated_data):

        try:

            for field ,values in validated_data.items():
                if hasattr(instance,field):
                    setattr(instance,field,values)

                    instance.save()

            return super().update(instance,validated_data)

        except Exception as e:
            raise serializers.ValidationError({'info': str(e)})    
        
    class Meta:
        model = UserProfile
        fields = ['country', 'state', 'city', 'address','profile_image']        



class UpdatePasswordSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(required=True)
    old_password = serializers.CharField(write_only = True, required=True)
    confirm_password = serializers.CharField(write_only = True,required=True)
    
    
    def validate(self,data):
        
        request = self.context.get('request')
        user = request.user
        
        if 'old_password' not in data:
            raise serializers.ValidationError({'password':'old_password is required'})

        if 'password' not in data:
            raise serializers.ValidationError({'password':'password is required'})

        if 'confirm_password' not in data:
            raise serializers.ValidationError({'password':'confirm_password is required'})
            
        if 'password' in data and 'confirm_password' in data and 'old_password' in data:
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            old_password = data.get('old_password')
            
            if old_password and not user.check_password(old_password):
                print(user.password)
                raise serializers.ValidationError({'Password': "Old password doesn't match"})
                
            if password != confirm_password:
                raise ValidationError('The passwords must match')
            
            validate_password_strength(password)
        return data
                
                
    def update(self,instance,validated_data):

        try:
            if 'password' in validated_data and 'old_password' in validated_data:
                old_password = validated_data.pop('old_password',None)
                password = validated_data.pop('password',None)
                

                if instance.check_password(old_password):
                    instance.set_password(password)
                    instance.save()
            
            return super().update(instance,validated_data)

        except Exception as e:
            raise serializers.ValidationError({'message':str(e)})
         
    class Meta:
        model = CustomUser
        fields = ['password','old_password','confirm_password']