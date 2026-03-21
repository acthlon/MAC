from django.shortcuts import render,redirect
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework_simplejwt.exceptions import TokenError 
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from django.conf import settings



def send_registration_email(request,user):
    
    token = default_token_generator.make_token(user)
    encoded_uuid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

    site_domain = get_current_site(request).domain

    verification_url = reverse('verify-email',kwargs={'user_id':encoded_uuid,'verification_token':token})

    final_verification_url = f'http://{site_domain}:8000/{verification_url}'

    

    # sending of e-mail
    subject = 'Activate your email'
    message = render_to_string('email/verification.html',{'user':user,'verification_url': final_verification_url})

    email_message = Mail(
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_emails=user.email,
        subject=subject,
        html_content=message,
        plain_text_content= f'hi {user.username}, click on the link above to verify your email'
    )

    api_key=settings.SENDGRID_API_KEY
    sg = SendGridAPIClient(api_key=api_key)
    response = sg.send(email_message)

    return response
    


def send_password_reset_email(user,request,email):
    

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
        from_email = settings.DEFAULT_FROM_EMAIL,
        to_emails = user.email,
        subject= subject,
        html_content=message 
    )

    api_key=settings.SENDGRID_API_KEY
    sg = SendGridAPIClient(api_key=api_key)
    response = sg.send(email_message)
    
    return response
