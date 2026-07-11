from django.template.loader import render_to_string 
from django.core.mail import send_mail
from django.conf import settings
from celery import shared_task
from accounts.models import CustomUser
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
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
        
    except CustomUser.DoesNotExist:
        # Don't retry if the user was deleted from the database
        return {"status": "failed", "message": "User does not exist"}
    except Exception as e:
        # Retry for actual email server connection issues
        raise self.retry(exc=e)



@shared_task(bind=True,max_retries=3, default_retry_delay=60)
def send_registration_email_task(self,user_id):

    try:
        user = get_object_or_404(CustomUser,  id=user_id)
        
        token = default_token_generator.make_token(user)

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

    except CustomUser.DoesNotExist:
        return {"status": "failed", "message": "User does not exist"}
    except Exception as e:
        raise self.retry(exc=e) 
    

@shared_task(bind=True,max_retries=3,default_retry_delay=60)
def send_password_reset_email_task(self,user_id,email):

    try:
        
        user = CustomUser.objects.get(id=user_id)
        token = default_token_generator.make_token(user)

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
    
    except CustomUser.DoesNotExist:
        return {"status": "failed", "message": "User does not exist"}
    except Exception as e:
        raise self.retry(exc=e)