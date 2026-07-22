from django.contrib.auth import authenticate, login
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import CustomUser
from accounts.serializers import (CustomUserSerializer,
                                  UpdatePasswordSerializer,
                                  UpdateUserProfileSerializer,
                                  UserProfileSerializer)
from accounts.tasks import (send_password_reset_email_task,
                            send_registration_email_task)


class RegistrationView(APIView):
    

    permission_classes = [AllowAny,]

    def post(self,request):

        serializer = CustomUserSerializer(data=request.data,context={'request':request})

        serializer.is_valid(raise_exception=True)
        user = serializer.save()
            
        # the email verification aspect
        # parameters needed

        send_registration_email_task.delay(user.id)
        
        return Response({'message':f'registration was successful, check your e-mail for verification'}, status=status.HTTP_201_CREATED)
    

class VerifyEmailView(APIView):


    permission_classes = [AllowAny,]

    def get(self,request,user_id,verification_token):
        try:

            user = get_object_or_404(CustomUser,pk=user_id)

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
        
        email= request.data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            resend_email = request.query_params.get('resend_email',None)

            if user is not None and resend_email == None: 
                send_password_reset_email_task.delay(user.id,email)

                return Response({'message': f'password reset link has been sent to your email'}, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:    
            return Response({'message': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)                    
            
            
    def get(self,request):

        resend_email = request.query_params.get('resend_email',None)
        
        try:
            user = CustomUser.objects.get(email=resend_email)
            if resend_email == user.email:
                send_password_reset_email_task.delay(user.id,resend_email)
                
                return Response({'message': 'a new reset link has been sent to your e-mail'}, status=status.HTTP_200_OK)                 

        except CustomUser.DoesNotExist:
            return Response({'message': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        

class PasswordResetConfirmView(APIView):

    permission_classes = [AllowAny,]

    def post(self,request,user_id,password_reset_token):

        try:
            user = CustomUser.objects.get(pk=user_id)

            if default_token_generator.check_token(user,password_reset_token):

                new_password = request.data.get('password') 
                confirm_password = request.data.get('confirm_password')

                if not new_password or not confirm_password:
                    return Response({'message': 'Both password fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

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

                login(request,user)
                token = RefreshToken.for_user(user)

                return Response({
                    'access_token': str(token.access_token),
                    'refresh_token' : str(token)
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({'message':'Invalid credentials, Please enter the correct email and password'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:    
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):

    permission_classes = [AllowAny,]

    def post(self,request):
        refresh_token = request.data.get('refresh_token')
        
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
# cache
                token.blacklist()

                return Response({'message':'Logout successful'},status=status.HTTP_200_OK)
            
            else:
                return Response({'message':'rfresh token not provided'})

        except TokenError:
            return Response({'messsage':'invalid token'}, status=status.HTTP_400_BAD_REQUEST)    


class UserProfileView(generics.RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated,]

    def get_object(self):

        user = self.request.user
        return user

    def get_serializer_class(self):
         
        if self.request.method in ['PUT','PATCH']:
            return UpdateUserProfileSerializer
        return  UserProfileSerializer

    
class UpdatePasswordView(generics.UpdateAPIView):
    
    permission_classes = [IsAuthenticated]
    serializer_class = UpdatePasswordSerializer
    
    # Forcefully disable PATCH so partial=True can NEVER happen!
    http_method_names = ['put', 'options'] 
    
    def get_object(self):
        user = self.request.user
        return user