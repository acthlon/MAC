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
from django.conf import settings
from order.models import Order
from payments.models import RefundRequest
from django.utils.html import strip_tags









@shared_task(bind=True,max_retries=3,default_retry_delay=60)
def send_order_confirmation_email_task(self,order_id,user_id):
   
   
    user = CustomUser.objects.get(id=user_id)
    order = Order.objects.get(id=order_id)
   
    try:
        subject = f'Order Confirmation - #{order.id}'
        context = {'order': order,
                   'user':user,
                   'orderitems':order.orderitems.all()}
        
        if order.status == 'CONFIRMED':
            html_message = render_to_string('email/order-confirm.html', context)
        elif order.status == 'FAILED':
            html_message = render_to_string('email/order-failed.html', context)

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
        print(f"Error sending confirmation email: {str(e)}")
        raise self.retry(exc=e) 
   

   
   

@shared_task(bind=True,max_retries=3,default_retry_delay=60)
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
        

        
        if order.status == "SHIPPED":
            html_message = render_to_string('email/order/order-shipped.html',context)
        
        elif order.status == "COMPLETED":
            html_message = render_to_string('email/order/order-completed.html',context)
        
        elif order.status == "CANCELED":
            html_message = render_to_string('email/order/order-cancelled.html',context)
        
        elif order.status == "RETURNED":
            html_message = render_to_string('email/order/order-returned.html',context)
            
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