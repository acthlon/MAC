from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated 
from rest_framework.views import APIView
from order.models import Order,PaymentMethod
from django.shortcuts import get_object_or_404
from payments.serializers import InitiatePaymentSerializer
from rest_framework.response import Response
from rest_framework import status
from paystackapi.transaction import Transaction
from django.conf import settings
from payments.models import Payment
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.csrf import csrf_exempt
import json
import hmac
import hashlib
import json
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from notifications.tasks import send_order_confirmation_email_task,send_order_status_update_email_task





class initializePaymentAPIView(APIView):

    permission_classes = [IsAuthenticated,]
    
    def post(self,request,pk):
        
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
        
        user = request.user
        order_id = pk
        order = get_object_or_404(Order,id=order_id, user=user,status='CREATED')
        payment_method = PaymentMethod.objects.get(code=serializer.validated_data['method_code'])
        
        
        payment = Payment.objects.create(
            user=request.user,
            order=order,
            payment_method=payment_method,
            amount=order.total_amount,
            currency='NGN'
        )        
        
            
        if payment.payment_method.code == 'PAYSTACK':

            amount_in_kobo = int(order.total_amount * 100)
            transaction = Transaction(secret_key=settings.PAYSTACK_SECRET_KEY)
            
            site_domain = get_current_site(request).domain
            
            url = reverse('payment-callback')
            callback_url = f"http://{site_domain}:8000/{url}"
                
            response = transaction.initialize(
                email=user.email,
                amount=amount_in_kobo,
                reference=str(payment.id),
                currency='NGN',
                callback_url=callback_url,
                metadata={
                    'order_id':str(order.id),
                    'payment_id':str(payment.id)
                },
                label=f"Checkout_{order.id}"
            )
            
            if response['status']:
                order.payment_reference = response['data']['reference']
                payment.reference = response['data']['reference']
                order.save()
                payment.save()
                return Response({
                    "authorization_url": response['data']['authorization_url'],
                    "reference": response['data']['reference']
                })

            else:
                payment.status = 'FAILED'
                payment.save()
                return Response({"detail": "Payment initialization failed"}, status=400)

        elif payment.payment_method == 'CASH_ON_dELIVERY':

            order.status = 'CONFIRMED'
            order.save()
        return Response(payment,response,status=status.HTTP_200_OK)


# class PaymentCallbackAPIView(APIView):
    
#     permission_classes = [IsAuthenticated,] 
    
#     def get(self, request):

#         reference = request.query_params.get('reference')
#         payment = get_object_or_404(Payment, reference=reference)
#         transaction = Transaction(secret_key=settings.PAYSTACK_SECRET_KEY)
#         response = transaction.verify(reference=reference)

#         if response['status'] and response['data']['status'] == 'success':
#             # payment.status = 'SUCCESSFUL'
#             # payment.save()
#             # payment.order.status = 'CONFIRMED'
#             # payment.order.save()
#             return Response({"message": "Payment successful",'response':response},status=status.HTTP_200_OK)
#         else:
#             # payment.status = 'FAILED'
#             # payment.save()
#             return Response({"message": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
        
class PaymentCallbackAPIView(APIView):
    
    def get(self, request):
        reference = request.query_params.get('reference')
        
        if reference:
            payment = get_object_or_404(Payment,reference=reference)
            # print({'payment':payment})
            
            if payment:
     
                if payment.status == 'SUCCESSFUL':

                    # print({'message':'payment-email sent successfully'})
                    return Response({"message": "Payment successful — order confirmed!"})

                elif payment.status == 'FAILED':
                    return Response({"message": "Payment failed — please try again"})
                
                elif payment.status == 'PENDING':
                    return Response({"message": "Payment pending — we'll notify you soon"},)
                
        return Response({"message": "Invalid reference"})    
    
    

@require_POST
@csrf_exempt
def paystack_webhook(request):

    request_body = request.body
    secret = settings.PAYSTACK_SECRET_KEY.encode()

    signature = request.headers.get('x-paystack-signature')
    if not signature:
        return Response(status=400)

    expected_signature = hmac.new(secret, request_body, hashlib.sha512).hexdigest()
    if signature != expected_signature:
        return Response(status=400)

    # Parse event
    try:
        post_response = json.loads(request_body)

    except json.JSONDecodeError:
        return Response(status=400)


    if post_response['event'] == 'charge.success':
        # print(post_response)
        
        reference = post_response['data']['reference']

        payment = get_object_or_404(Payment, reference=reference)

        
        if payment.status != 'SUCCESSFUL':
            # print(payment.status)
            payment.status = 'SUCCESSFUL'
            payment.save()

            # send_order_confirmation_email(payment.order,payment.user) 
            #_task(payment.user)
            
            order = payment.order

            # Deduct stock from all order items
            for order_item in order.orderitems.all():
                # print(order_item)
                
                item = order_item.content_object 
                # print(item.stock)
                item.stock -= order_item.quantity
                item.save()
            
            
            # print(order.status)
            # print(order.payment_status)
            order.status = 'CONFIRMED'
            order.payment_status = 'SUCCESSFUL'
            order.save()
            # print(order)
            
                        
    return HttpResponse(status=200)                  
