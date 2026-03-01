from django.template.loader import render_to_string 
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from decouple import config 
from rest_framework.response import Response
from rest_framework import status
from django.utils.html import strip_tags


def send_welcome_email(user):
    
        try:    
            html_message = render_to_string('email/welcome-email.html',
            {'user':user})
            plain_message = strip_tags(html_message)
            subject = "Welcome to Our Store "
            

            email_message = Mail(
                from_email = config("DEFAULT_FROM_EMAIL"),
                to_emails = user.email,
                subject= subject,
                html_content=html_message, 
            )

            api_key=config("SENDGRID_API_KEY")
            sg = SendGridAPIClient(api_key=api_key)
            response = sg.send(email_message)


            if response.status_code == 202:
                print({'message': 'Email sent successfully'})
            
            else:
                print({'message': 'Email not sent successfully'})
            
            return Response({'message':'invalid or expired token'},status = status.HTTP_400_BAD_REQUEST)

            
        except Exception as e:
            return Response({'message': str(e)},status=status.HTTP_400_BAD_REQUEST)    





def send_order_confirmation_email(order,user):
   
   try: 
        subject = f'Order Confirmation - #{order.id}'
        context = {'order': order,
                   'user':user}
        
        html_message = render_to_string('email/order-confirmation.html', context)


        email_message = Mail(
            from_email = config("DEFAULT_FROM_EMAIL"),
            to_emails = user.email,
            subject= subject,
            html_content=html_message, 
        )
        
        api_key=config("SENDGRID_API_KEY")
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(email_message)

        
        if response.status_code == 202:

            print({'message':'payment-email worked nommmmm'})
            # return Response({'message':f'E-mail sent successfully'}, status=status.HTTP_201_CREATED)
        
        else:
            print({'message':'payment-email worked'})
            # return Response({'message':'Error in sending mail'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
   except Exception as e:
       return Response({'message':str(e)},status=status.HTTP_400_BAD_REQUEST)
   
   

def send_order_status_update_email(order,new_status,user):
    
    try:
        subject = f'Order Update - #{order.id} - {new_status}'
        
        context = {
            'order' : order,
            'status' : new_status,
            'user':user
        }
        
        html_message = render_to_string('email/order-status.html',context)
        
        # email_message = Mail(
        #     subject = subject,
        #     to_emails = order.user.email,
        #     from_email = config('DEFAULT_FROM_EMAIL'),
        #     message = html_message,
        # )
        
        # api_key = config('SENDGRID_API_KEY')
        # sg = SendGridAPIClient(api_key=api_key)
        # response = sg.send(email_message)


        email_message = Mail(
            from_email = config("DEFAULT_FROM_EMAIL"),
            to_emails = user.email,
            subject= subject,
            html_content=html_message, 
        )
        
        api_key=config("SENDGRID_API_KEY")
        sg = SendGridAPIClient(api_key=api_key)
        response = sg.send(email_message)

        if response.status_code == 202:

            print({'message':'order updated successfully'})
            return Response({'message':f'E-mail sent successfully order updated successfully'}, status=status.HTTP_201_CREATED)
        
        else:
            return Response({'message':'Error in sending mail'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
       return Response({'message':str(e)},status=status.HTTP_400_BAD_REQUEST)    
    