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





@shared_task(bind=True,max_retries=3, default_retry_delay=60)
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
            'site_url': site_url,
        }
        


        if refund_request.status == 'UNDER_REVIEW':
            html_message = render_to_string('email/refund/refund-review.html',context=context)
        
        elif refund_request.status == 'APPROVED':
            html_message = render_to_string('email/refund/refund-approved.html',context=context)
            
        elif refund_request.status == 'REJECTED':
            html_message = render_to_string('email/refund/refund-rejected.html',context=context)
        
        elif refund_request.status == 'COMPLETED':
            html_message = render_to_string('email/refund/refund-completed.html',context=context)
        
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[refund_request.user.email],
            html_message=html_message,
            fail_silently=False,
        )

        print(f"Refund success email sent to {refund_request.user.email}")
        return True

    except Exception as e:
        print(f"Failed to send refund success email: {str(e)}")
        raise self.retry(exc=e) 