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
from notifications.tasks import send_registration_email_task,send_password_reset_email_task


def send_registration_email(request,user):
    
    send_registration_email_task(request,user)
   
    


def send_password_reset_email(user,request,email):
    
    send_registration_email_task(user,request,email)