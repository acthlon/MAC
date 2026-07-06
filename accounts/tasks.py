from django.template.loader import render_to_string 
from django.core.mail import send_mail
from decouple import config 
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from celery import shared_task
from django.contrib.sites.models import Site
from accounts.models import CustomUser
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError 
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from django.conf import settings
from order.models import Order
from payments.models import RefundRequest
from django.utils.html import strip_tags






@shared_task(bind=True,max_retries=3, default_retry_delay=60)
def send_welcome_email_task(self,user_id):
    
    user = get_object_or_404(CustomUser, id=user_id)
    try:    
        html_message = render_to_string('email/accounts/welcome-email.html',
        {'user':user})
        plain_message = strip_tags(html_message)

        subject = "Welcome to Our Store "
        

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return {"status": "sent",
                "email": user.email,
                "status_code": 200,
                "message": "Email sent successfully"}
        
    except Exception as e:
        raise self.retry(exc=e)
    





@shared_task(bind=True,max_retries=3, default_retry_delay=60)
def send_registration_email_task(self,user_id):

    try:
        user = get_object_or_404(CustomUser,  id=user_id)
        
        token = default_token_generator.make_token(user)
        # encoded_uuid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

        site_domain = settings.SITE_URL

        verification_url = reverse('verify_email',kwargs={'user_id':user_id,'verification_token':token})

        final_verification_url = f'{site_domain}{verification_url}'

        

        # sending of e-mail
        subject = 'Activate your email'
        html_message = render_to_string('email/accounts/verification.html',{'user':user,'verification_url': final_verification_url})
        plain_message = strip_tags(html_message)
        
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "sent", "email": user.email, "status_code":200,"message":"Registration link sent successfully"}

    except Exception as e:
        raise self.retry(exc=e) 



    

@shared_task(bind=True,max_retries=3,default_retry_delay=60)
def send_password_reset_email_task(self,user_id,email):

    try:
        
        user = CustomUser.objects.get(id=user_id)

        token = default_token_generator.make_token(user)
        # encoded_uuid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

        password_reset_link = reverse('password_reset_confirm',kwargs={'password_reset_token':token,'user_id':user_id})
        password_resend_link = reverse('password_reset_request') 
        
        site_domain = settings.SITE_URL

        password_reset_url = f'{site_domain}{password_reset_link}'
        password_resend_url = f'{site_domain}{password_resend_link}?resend_email={email}'

        html_message = render_to_string('email/accounts/password-reset.html',{'password_reset_url': password_reset_url,'password_resend_url': password_resend_url,
        'user':user})
        subject = "Reset Your Password"

        plain_message = strip_tags(html_message)


        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        
        return {"status": "sent", "email": user.email, "status_code": 200}
    
    except Exception as e:
        raise self.retry(exc=e) 