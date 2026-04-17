import uuid

from decouple import config
from django.contrib.auth import authenticate, login
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from accounts.models import CustomUser
from accounts.serializers import (
    CustomUserSerializer,
    UpdatePasswordSerializer,
    UpdateUserProfileSerializer,
    UserProfileSerializer
)
from core.permissions import IsOwnerOrReadOnly
from notifications.tasks import (
    send_password_reset_email_task,
    send_registration_email_task
)


class RegistrationView(APIView):
    

    permission_classes = [AllowAny,]

    def post(self,request):

        serializer = CustomUserSerializer(data=request.data,context={'request':request})
        if serializer.is_valid():
            user = serializer.save()
            send_registration_email_task.delay(user.id)
            return Response({'message':f'registration was successful, check your e-mail for verification'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

    

class VerifyEmailView(APIView):


    permission_classes = [AllowAny,]

    def get(self,request,user_id,verification_token):
        try:

            decoded_bytes = urlsafe_base64_decode(user_id)

            decoded_uuid_str = decoded_bytes.decode('utf-8')

            decoded_uuid = uuid.UUID(decoded_uuid_str) 

            user = get_object_or_404(CustomUser,pk=decoded_uuid)

            if default_token_generator.check_token(user,verification_token):

                user.is_active = True
                user.save(update_fields=['is_active'])     


                return Response({'messsage':'verification was successful, your account is now active and you can proceed to login'}, status=status.HTTP_200_OK)

            else:
                return Response({'message':'invalid or expired token'}, status = status.HTTP_400_BAD_REQUEST)


        except Exception as e:
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class PasswordResetRequestView(APIView):

    permission_classes = [AllowAny,]

    def post(self,request):

        try:

            email= request.data.get('email')
            user = CustomUser.objects.get(email=email)
            resend_email = request.query_params.get('resend_email',None)

            if user is not None: 
            
                if resend_email == None:
                    try:
                        send_password_reset_email_task.delay(user.id,email)
                    except Exception as e:
                        return Response({'message': str(e)},status=status.HTTP_400_BAD_REQUEST)
                    

                    return Response({'message': f'password reset link has been sent to your email'}, status=status.HTTP_200_OK)

        except Exception as e:    
            return Response({'message':str(e)} , status=status.HTTP_404_NOT_FOUND)                    
            
    def get(self,request):

        resend_email = request.query_params.get('resend_email',None)
        user = CustomUser.objects.get(email=resend_email)
        
        try:

            if resend_email == user.email:
                email=resend_email
                send_password_reset_email_task.delay(user.id,email)
                return Response({'message': 'a new reset link has been sent to your e-mail'})                 

                
        except Exception as e:
            return Response({'message':str(e)} , status=status.HTTP_404_NOT_FOUND)
        




class PasswordResetConfirmView(APIView):
    
    permission_classes = [AllowAny,]

    def post(self,request,user_id,password_reset_token):

        try:
            decode_uuid = urlsafe_base64_decode(user_id)

            decoded_uuid_str = decode_uuid.decode('utf-8')

            user_uuid = uuid.UUID(decoded_uuid_str) 

            user = CustomUser.objects.get(pk=user_uuid)

            serializer = CustomUserSerializer(data=request.data)

            if default_token_generator.check_token(user,password_reset_token):

                new_password = request.data.get('password') 
                confirm_password = request.data.get('confirm password')

                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()
                    return Response({'message':'password set successfully'},status=status.HTTP_200_OK)
            
                else:
                    return Response({'message': 'Ensure both password fields are the same'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'message':'invalid token or token expired, request for a new token'}, status=status.HTTP_400_BAD_REQUEST)
              
        except Exception as e:
                return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny,]

    def post(self,request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            user = authenticate(email=email,password=password)
          
            if user is not None:

                # login(request,user)
                token = RefreshToken.for_user(user)

                return Response({
                    'access_token': str(token.access_token),
                    'refresh_token' : str(token)
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({'message':'invalid credentials, user with this email does not exist, proceed to signup'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:    
            print(f'{user.email}')
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)



class RefreshTokenView(APIView):

    permission_classes = [AllowAny,]

    def post(self,request):
        refresh_token = request.data.get('refresh_token')
        print(refresh_token)
        
        try:
            if not refresh_token:
                return Response({'message':'Refresh token is required'},status = status.HTTP_400_BAD_REQUEST)
            
            else:
                refresh = RefreshToken(refresh_token)
                access_token = str(refresh.access_token) 

                return Response({"access_token": access_token},status=status.HTTP_200_OK)

        except TokenError as e:
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    
    permission_classes = [IsAuthenticated,]

    def post(self,request):

        try:

            refresh_token = request.data.get('refresh_token')

            if refresh_token:

                token = RefreshToken(refresh_token)
                
                token.blacklist()

                return Response({'message':'Logout successful'},status=status.HTTP_200_OK)
            
            else:
                return Response({'message':'rfresh token not provided'})

        except TokenError:
            return Response({'messsage':'invalid token'}, status=status.HTTP_400_BAD_REQUEST)    




# class UserProfileView(APIView):

#     permission_classes = [IsAuthenticated,]

#     def get(self,request,pk):

#         user = request.user
#         profile = user.userprofile
  
#         serializer = UserProfileSerializer(profile)

#         return Response(serializer.data, status=status.HTTP_200_OK)


#     def put(self,request,pk):
        
#         try:
            
#             user = request.user
#             profile = user.userprofile
#             print(profile)
#             serializer = UpdateUserProfileSerializer(profile,data = request.data, partial=True, context = {'request':request})
            
#             if serializer.is_valid():
#                 print(serializer.validated_data)
#                 serializer.save()
#                 return Response({'status':'success',
#                                  'message':'Profile Updated successfully',
#                                  'data':serializer.data})
#             else:
#                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         except Exception as e:
#             return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)    



class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UpdateUserProfileSerializer
    permission_classes = [IsAuthenticated,]

    def get_object(self):
        return self.request.user





class UpdatePasswordView(APIView):
    
    def put(self,request, *args, **kwargs):
        user = request.user
        data = request.data

        serializer = UpdatePasswordSerializer(user,data=request.data,context={'request':request})
        serializer.is_valid(raise_exception=True)
        response_data = serializer.update(user, data)
        return Response(response_data,status=status.HTTP_200_OK)
    