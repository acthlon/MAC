import uuid
from django.shortcuts import render,redirect
from rest_framework.response import Response 
from rest_framework.views import APIView
from rest_framework import status
from accounts.models import CustomUser,UserProfile
from django.contrib.auth import authenticate,login
from rest_framework_simplejwt.tokens import RefreshToken 
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import get_object_or_404
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from accounts.serializers import CustomUserSerializer,UserProfileSerializer
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError 
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from rest_framework.permissions import IsAuthenticated,AllowAny
from decouple import config
from django.utils import timezone
from django.utils.encoding import force_bytes 
from core.permissions import IsOwnerOrReadOnly




class RegistrationView(APIView):
    

    permission_classes = [AllowAny,]

    def post(self,request):

        serializer = CustomUserSerializer(data=request.data,context={'request':request})
        # try:

        if serializer.is_valid():
            user = serializer.save()
            
            # the email verification aspect
            # parameters needed
        
            token = default_token_generator.make_token(user)
            encoded_uuid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

            site_domain = get_current_site(request).domain

            verification_url = reverse('verify-email',kwargs={'user_id':encoded_uuid,'verification_token':token})

            final_verification_url = f'http://{site_domain}:8000/{verification_url}'

            

            # sending of e-mail
            subject = 'Activate your email'
            message = render_to_string('email/verification.html',{'user':user,'verification_url': final_verification_url})

            email_message = Mail(
                from_email=config("DEFAULT_FROM_EMAIL"),
                to_emails=user.email,
                subject=subject,
                html_content=message,
                plain_text_content= f'hi {user.username}, click on the link above to verify your email'
            )

            api_key=config("SENDGRID_API_KEY")
            sg = SendGridAPIClient(api_key=api_key)
            response = sg.send(email_message)
            
            if response.status_code == 202:

                return Response({'message':f'registration was successful, check your e-mail for verification'}, status=status.HTTP_201_CREATED)
            
            else:
                return Response({'message':'Error in sending mail'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     return Response({'message':str(e)},status=status.HTTP_400_BAD_REQUEST)
    

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

                return Response({'messsage':'verification was successful, your account is now active and you can proceed to login'}, status=status.HTTP_400_BAD_REQUEST)
            
            else:
                return Response({'message':'invalid or expired token'}, status = status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class PasswordResetRequestView(APIView):

    permission_classes = [AllowAny,]

    def send_email(self,user,request,email):
        try:

            token = default_token_generator.make_token(user)
            encoded_uuid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

            password_reset_link = reverse('password-reset-confirm',kwargs={'password_reset_token':token,'user_id':encoded_uuid})
            password_resend_link = reverse('password-reset-request') 
            site_domain = get_current_site(request).domain

            password_reset_url = f'http://{site_domain}:8000/{password_reset_link}'
            password_resend_url = f'http://{site_domain}:8000{password_resend_link}?resend_email={email}'

            message = render_to_string('email/password-reset.html',{'password_reset_url': password_reset_url,'password_resend_url': password_resend_url,
            'user':user})
            subject = "Reset Your Password"

            email_message = Mail(
                from_email = config("DEFAULT_FROM_EMAIL"),
                to_emails = user.email,
                subject= subject,
                html_content=message 
            )

            api_key = config("SENDGRID_API_KEY")
            sg = SendGridAPIClient(api_key=api_key)
            response = sg.send(email_message)
        except Exception as e:
            return Response({'message': str(e)},status=status.HTTP_400_BAD_REQUEST)    

    

    def post(self,request):

        try:

            email= request.data.get('email')
            user = CustomUser.objects.get(email=email)
            resend_email = request.query_params.get('resend_email',None)

            if user is not None: 
            
                if resend_email == None:

                    self.send_email(user,request,email)
                    return Response({'message': f'password reset link has been sent to your email'}, status=status.HTTP_200_OK)
            
        except Exception as e:    
            return Response({'message':str(e)} , status=status.HTTP_404_NOT_FOUND)                    
            
    def get(self,request):

        resend_email = request.query_params.get('resend_email',None)
        user = CustomUser.objects.get(email=resend_email)
        
        try:

            if resend_email == user.email:
                email=resend_email

                self.send_email(user,request,email)
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
                    return Response({'message': 'Ensure bth password fields are the same'}, status=status.HTTP_400_BAD_REQUEST)
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
# cache
                token.blacklist()

                return Response({'message':'Logout successful'},status=status.HTTP_200_OK)
            
            else:
                return Response({'message':'rfresh token not provided'})

        except TokenError:
            return Response({'messsage':'invalid token'}, status=status.HTTP_400_BAD_REQUEST)    




class UserProfileView(APIView):
    

    permission_classes = [IsOwnerOrReadOnly,]

    def get(self,request,pk):

        user = request.user
        try:
            profile = UserProfile.objects.get(user__id = pk)
        except UserProfile.DoesNotExist:
            return Response({'message':'Profile does not exist for this user'})    
        serializer = UserProfileSerializer(profile)

        return Response(serializer.data, status=status.HTTP_200_OK)


    def patch(self,request):
        
        try:

            serializer = UserProfileSerializer(data = request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({'status':'success',
                                 'message':'Profile Updated successfully',
                                 'data':serializer.data})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)    

  