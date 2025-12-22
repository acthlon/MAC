from django.shortcuts import render,redirect
from rest_framework.response import Response 
from rest_framework.views import APIView
from accounts.serializers import CustomUserSerializer
from rest_framework import status
from accounts.models import CustomUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken 
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .serializers import CustomUserSerializer
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError 




class RegistrationView(APIView):
    
    def post(self,request):

        serializer = CustomUserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # the email verification aspect
            # parameters needed
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(str(user.pk).encode())

            site_domain = get_current_site(request).domain

            verification_url = reverse('verify-email',kwargs={'user_id':uid,'verification_token':token})

            final_verification_url = f'https://{site_domain}/{verification_url}'

            # sending of e-mail

            subject = 'Activate your email'
            message = render_to_string('email/verification.html',{'user':user,'verification_url': final_verification_url})

            send_mail(subject,message,'no-reply@mysite.com',[user.email])

            return Response({'message':'registratin was successful, check your e-mail for verification'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
    

class VerifyEmailView(APIView):

    def get(self,request,user_id,verification_token):
        try:

            uid = urlsafe_base64_decode(user_id)
            user = get_object_or_404(CustomUser,pk=user_id)

            if default_token_generator.check_token(user,verification_token):

                user.is_active
                user.save()     

                return Response({'messsage':'verification was successful, your account is now active and you can proceed to login'}, status=status.HTTP_400_BAD_REQUEST)
            
            else:
                return Response({'message':'invalid or expired token'}, status = status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class PasswordResetRequestView(APIView):

    def post(self,request):
        try:

            email= request.data.get('email')
            user = CustomUser.objects.filter(email=email).first()

            if user:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(str(user.pk).encode())

                password_reset_link = reverse('password-reset-confirm',kwargs={'password_reset_token':token,'user_id':uid})

                site_domain = get_current_site(request).domain
                password_reset_url = f'https://{site_domain}{password_reset_link}'


                password_resend_url = f'https://{site_domain}{reverse('password-reset-requeest')}'
                subject = 'Password Recovery'
                message = render_to_string('email/password-reset.html',{'password_reset_url': password_reset_url,'password_resend_url': password_resend_url,})

                send_mail(subject,message,'no-reply@mydomain.com',[email])
                return Response({'message': 'password reset link has been sent to your email'}, status=status.HTTP_200_OKAY)
            else:
                return Response({'message':'user not found'}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
                
            return Response({'message':str(e)}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetConfirmView(APIView):

    def post(self,request,user_id,password_reset_token):

        try:
            uid = urlsafe_base64_decode(user_id)
            user = CustomUser.objects.get(pk=uid)


            if default_token_generator.check_token(user,password_reset_token):
                user.set_password(request.data.get('password'))
                user.save()

                return Response({'message':'password set successfully'},status=status.HTTP_200_OK)
            else:
                return Response({'message':'invalid token or token expired, request for a new token'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:

                return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):

    def post(self,request):

        try:

            email = request.data.get('email')
            password = request.data.get('password')
            user = authenticate(request,email=email,password=password)

            if user is not None:
                token = RefreshToken.for_user(user)

                return Response({
                    'access_token': str(token.access_token),
                    'refresh_token' : str(token)
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({'message':'invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:    
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    
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
        