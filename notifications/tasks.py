from django.template.loader import render_to_string 
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
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

import uuid





@shared_task(bind=True)
def send_welcome_email_task(self,user_id):
    
        user = get_object_or_404(CustomUser, id=user_id)
        try:    
            html_message = render_to_string('email/welcome-email.html',
            {'user':user})

            subject = "Welcome to Our Store "
            

            email_message = Mail(
                from_email = settings.DEFAULT_FROM_EMAIL,
                to_emails = user.email,
                subject= subject,
                html_content=html_message, 
            )

            api_key=settings.SENDGRID_API_KEY
            sg = SendGridAPIClient(api_key=api_key)
            response = sg.send(email_message)
            
            
            return {"status": "sent", "email": user.email, "status_code": response.status_code}
            
        except Exception as e:
            return ({'message': str(e)})    




@shared_task(bind=True)
def send_refund_confirmation_email(self,refund_id,user_id):    


    try:
        refund_request= RefundRequest.objects.get(id=refund_id, user=user_id)
        site_url = get_current_site('request')
        site_domain = Site.objects.get_current().domain
        site_url = f'http://{site_domain}:8000/'
        
        subject = f"Refund Processed Successfully - Order #{refund_request.order.id}"
            
        context={

            'user': refund_request.user,
            'order': refund_request.order,
            'reason': refund_request.reason,
            'refund_amount': refund_request.refund_amount,
            'processed_at': refund_request.processed_at,
            # 'site_url': "https://yourstore.com",
            'site_url': site_url,
        }
        
        html_message = render_to_string('email/refund.html',context=context)

        email_message = Mail(
            from_email = settings.DEFAULT_FROM_EMAIL,
            to_emails = refund_request.user.email,
            subject= subject,
            html_content=html_message, 
        )

        api_key=settings.SENDGRID_API_KEY
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(email_message)
        
        print(f"Refund success email sent to {refund_request.user.email}")
        return True

    except Exception as e:
        print(f"Failed to send refund success email: {str(e)}")
        return False
    
    
    
    

@shared_task(bind=True)
def send_order_confirmation_email_task(self,order_id,user_id):
   
   
    user = CustomUser.objects.get(id=user_id)
    order = Order.objects.get(id=order_id)
   
    try:
   
        subject = f'Order Confirmation - #{order.id}'
        context = {'order': order,
                   'user':user,
                   'orderitems':order.orderitems.all()}
        
        html_message = render_to_string('email/order-confirmation.html', context)


        email_message = Mail(
            from_email = settings.DEFAULT_FROM_EMAIL,
            to_emails = user.email,
            subject= subject,
            html_content=html_message, 
        )
        
        api_key=settings.SENDGRID_API_KEY
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(email_message)


        return {"status": "sent", "email": user.email, "status_code": response.status_code}
        
    except Exception as e:
        print(f"❌ Error sending confirmation email: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
   
   
   

   
   

@shared_task(bind=True)
def send_order_status_update_email_task(self,order_id,new_status,user_id):
    
    try:
        
        user = CustomUser.objects.get(id=user_id)
        order = Order.objects.get(id=order_id)
        subject = f'Order Update - #{order.id} - {new_status}'
        
        context = {
            'order' : order,
            'status' : new_status,
            'user':user
        }
        
        html_message = render_to_string('email/order-status.html',context)
        

        email_message = Mail(
            from_email = settings.DEFAULT_FROM_EMAIL,
            to_emails = user.email,
            subject= subject,
            html_content=html_message, 
        )
        
        api_key=settings.SENDGRID_API_KEY
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(email_message)

        return {"status": "sent", "email": user.email, "status_code": response.status_code}
    
    except Exception as e:
        return ({'message': str(e)}) 





@shared_task(bind=True)
def send_registration_email_task(self,user_id):

    try:
        user = get_object_or_404(CustomUser,  id=user_id)
        
        token = default_token_generator.make_token(user)
        encoded_uuid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

        site_domain = Site.objects.get_current().domain

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

        return {"status": "sent", "email": user.email, "status_code": response.status_code}

    except Exception as e:
        return ({'message': str(e)}) 
        # print(f"❌ ERROR sending email to user veriification e-maillllllllll {user_id}: {e}")
        # raise self.retry(exc=e, countdown=60, max_retries=3)



    

@shared_task(bind=True)
def send_password_reset_email_task(self,user_id,email):

    try:
        
        user = CustomUser.objects.get(id=user_id)

        token = default_token_generator.make_token(user)
        encoded_uuid = urlsafe_base64_encode(str(user.pk).encode('utf-8'))

        password_reset_link = reverse('password-reset-confirm',kwargs={'password_reset_token':token,'user_id':encoded_uuid})
        password_resend_link = reverse('password-reset-request') 
        
        site_domain = Site.objects.get_current().domain

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
        
        return {"status": "sent", "email": user.email, "status_code": response.status_code}
    
    except Exception as e:
        return ({'message': str(e)})    