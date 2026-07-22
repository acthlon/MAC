import hashlib
import hmac
import json

from celery import shared_task
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from paystackapi.refund import Refund
from paystackapi.transaction import Transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from order.models import Order, PaymentMethod
from payments.models import Payment, RefundRequest
from payments.serializers import (InitiatePaymentSerializer,
                                  RefundRequestSerializer,
                                  RefundRequestUpdateSerializer)


class initializePaymentAPIView(APIView):

    permission_classes = [IsAuthenticated,]
    
    def post(self,request,pk):
        
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():

            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
        
        user = request.user
        order_id = pk
        order = get_object_or_404(Order,id=order_id,status='CREATED')
        payment_method = PaymentMethod.objects.get(code=serializer.validated_data['method_code'])
        
        print(order)
        
        
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
            
            url = reverse('payment_callback')
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
        print('reference')
        
        if reference:
            payment = get_object_or_404(Payment,reference=reference)
            print({'payment':payment})
            
            if payment:
     
                if payment.status == 'SUCCESSFUL':

                    # print({'message':'payment-email sent successfully'})
                    return Response({"message": "Payment successful — order confirmed!"})

                elif payment.status == 'FAILED':
                    return Response({"message": "Payment failed — please try again"})
                
                elif payment.status == 'PENDING':
                    return Response({"message": "Payment pending — we'll notify you soon"},)
                
        return Response({"message": "Invalid reference"})    
    
    

# @require_POST
# @csrf_exempt
# def paystack_webhook(request):

#     request_body = request.body
#     secret = settings.PAYSTACK_SECRET_KEY.encode()

#     signature = request.headers.get('x-paystack-signature')
#     if not signature:
#         return Response(status=400)

#     expected_signature = hmac.new(secret, request_body, hashlib.sha512).hexdigest()
#     if signature != expected_signature:
#         return Response(status=400)

#     # Parse event
#     try:
#         post_response = json.loads(request_body)

#     except json.JSONDecodeError:
#         return Response(status=400)


#     if post_response['event'] == 'charge.success':
#         # print(post_response)
        
#         reference = post_response['data']['reference']

#         payment = get_object_or_404(Payment, reference=reference)

        
#         if payment.status != 'SUCCESSFUL':
#             # print(payment.status)
#             payment.status = 'SUCCESSFUL'
#             payment.save()

#             # send_order_confirmation_email(payment.order,payment.user) 
#             #_task(payment.user)
            
#             order = payment.order

#             # Deduct stock from all order items
#             for order_item in order.orderitems.all():
#                 # print(order_item)
                
#                 item = order_item.content_object 
#                 # print(item.stock)
#                 item.stock -= order_item.quantity
#                 item.save()
            
            
#             # print(order.status)
#             # print(order.payment_status)
#             order.status = 'CONFIRMED'
#             order.payment_status = 'SUCCESSFUL'
#             order.payment_reference = payment.reference
#             order.save(update_fields=['status', 'payment_status', 'payment_reference'])
#             # print(order)
            
                        
#     return HttpResponse(status=200)                  









@require_POST
@csrf_exempt
def paystack_webhook(request):
    
    # Verify Paystack signature
    request_body = request.body
    secret = settings.PAYSTACK_SECRET_KEY.encode()
    signature = request.headers.get('x-paystack-signature')

    if not signature:
        return Response(status=400)

    expected_signature = hmac.new(secret, request_body, hashlib.sha512).hexdigest()
    
    if signature != expected_signature:
        return Response(status=400)

    # Parse the webhook data
    try:
        post_response = json.loads(request_body)
        
        print(post_response)
        
        print('post_response')
    except json.JSONDecodeError:
        return Response(status=400)
    
    

    # all the aove are stll security check below is the processing of the real handling of successful payment
    if post_response['event'] == 'charge.success':
        print('post_response')
        
        data = post_response['data']
        reference = data['reference']
        
        authorization = data.get('authorization', {})

        card_brand = authorization.get('brand')  # e.g. "visa", "mastercard"
        card_bin = authorization.get('bin')      # First 6 digits
        card_last4 = authorization.get('last4')  # Last 4 digits
        card_type = authorization.get('card_type')
        exp_month = authorization.get('exp_month')
        exp_year = authorization.get('exp_year')
        auth_code = authorization.get('authorization_code')

        payment = get_object_or_404(Payment, reference=reference)

        # Prevent processing the same payment multiple times
        if payment.status != 'SUCCESSFUL':
            
            # Update payment status
            payment.status = 'SUCCESSFUL'
            payment.card_brand = card_brand
            payment.card_bin = card_bin
            payment.card_last4 = card_last4
            payment.authorization_code = auth_code
            payment.save()

            order = payment.order

            # Deduct stock from products
            for order_item in order.orderitems.all():
                item = order_item.content_object
                if item.stock >= order_item.quantity:
                    item.stock -= order_item.quantity
                    item.save()

            # Update order status - This is the most important part
            order.status = 'CONFIRMED'
            order.payment_status = 'SUCCESSFUL'
            order.payment_reference = payment.reference
            order.save(update_fields=['status', 'payment_status', 'payment_reference'])

            print(f"✅ Order #{order.id} has been confirmed successfully.")

    return HttpResponse(status=200)



class CreateRefundRequestAPIView(APIView):
    
    permission_classes = [IsAuthenticated,]
    
    def post(self,request,order_id):
        order = get_object_or_404(Order,id=order_id,user=request.user)
        
        if order.delivery_status != 'DELIVERED':
            return Response({"error": "You can only request return for delivered orders"},status=status.HTTP_400_BAD_REQUEST)
        
        if order.return_requests.first() == None:
            
            try:
                
                serializer = RefundRequestSerializer(data=request.data,context={'request':request,'order':order})

                if serializer.is_valid(): 
                    serializer.save()
                
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({'error':str(e)},status=status.HTTP_400_BAD_REQUEST)

        return Response({'message' : 'A refund request has been made for this order already'},status=status.HTTP_400_BAD_REQUEST)

class ReturnRequestActionAPIView(APIView):
    
    def patch(self,request,return_id):
        
        refund_request = get_object_or_404(RefundRequest,id=return_id)
        
        serializer = RefundRequestUpdateSerializer(refund_request,data = request.data, context = {'request':request},partial=True,)

        
        if serializer.is_valid():
            updated_request = serializer.save()
            

            
            print('THIS IS WONDERFUL STAGE TOPPPPPP')
            # refund payment processing
            if updated_request.status == 'APPROVED':
                print('THIS IS WONDERFUL STAGE   111111')
                
                try:
                    order_id=updated_request.order.id 
                   
                    payment_processing = process_paystack_refund.delay(refund_id=return_id,order_id=order_id)
                    print('THIS IS WONDERFUL STAGE   111EXTEA')
                
                except Exception as e:
                    return Response({'error': str(e)},status=status.HTTP_400_BAD_REQUEST)
                
            return Response(serializer.data,status=status.HTTP_200_OK)
            
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)   
        

 # NB: if you are using bind=true, then you must use self as an argument in the functin below else you will be having ths error       {"error":"process_paystack_refund() takes 1 positional argument but 2 were given"}
 
#  i later removed @shared_task from here because i am not sending e-mail but the principle still applied assumng this function is fr  sending e-mail

# @shared_task(bind=True)
# def process_paystack_refund(self,order_id):
    
#     order = get_object_or_404(Order,id=order_id)
#     try:
#         refund = Refund(secrete_key=settings.PAYSTACK_SECRET_KEY)
#         payment_response = refund.create(
#         reference = order.payment_reference,
#         amount = int(order.total_amount * 100)   
#         )
        
#         print('THE MESSAGE: This actually worked')
#         print(f'ANOTHER MESSAGE:{payment_response.get('status')}:')
#         return payment_response.get('status','false')
    
#     except Exception as e:
#         print({'EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE':{str(e)}})





@shared_task(bind=True)
def process_paystack_refund(self, order_id,refund_id):
    
    try:
        order = Order.objects.get(id=order_id)
        refund_request = RefundRequest.objects.get(id=refund_id)

        print(f"[Refund Test] Starting refund for order {order_id}")
        print(f"[Refund Test] Reference: {order.payment_reference}")
        print(f"[Refund Test] Amount: {order.total_amount} NGN")

        refund_api = Refund(secret_key=settings.PAYSTACK_SECRET_KEY)

        response = refund_api.create(
            transaction=order.payment_reference,
            amount=int(order.total_amount * 100),
            reason=refund_request.reason
        )

        print(f"[Refund Test] Full Paystack Response: {response}")

        success = response.get('status', False)
        message = response.get('message', 'No message')

        if success:
            print(f"[Refund SUCCESS] Order {order_id}")
            
            for item in order.orderitems.all():
                item.content_object.stock += item.quantity
                item.content_object.save()
                
                refund_request.status = 'COMPLETED'
                refund_request.save()
                
                print('THIS IS WONDERFUL STAGE 33333 PRODUCTS UPDATED SUCCCESSFULLY')
        else:
            print(f"[Refund FAILED] Order {order_id} - Message: {message}")


    except Exception as e:
        print(f"[Refund ERROR] Order {order_id}: {str(e)}")
        return False



# class ReturnRequestActionAPIView(APIView):
#     # permission_classes = [IsAdminUser]

#     def patch(self, request, return_id):
#         refund_request = get_object_or_404(RefundRequest, id=return_id)

#         serializer = RefundRequestUpdateSerializer(
#             refund_request, 
#             data=request.data, 
#             partial=True
#         )

#         if serializer.is_valid():
#             # This is the correct way
#             updated_request = serializer.save()

#             if updated_request.status == 'approved':
#                 refund_success = process_paystack_refund.delay(updated_request.order)

#                 if refund_success:
#                     # Return stock
#                     for item in updated_request.order.orderitems.all():
#                         product = item.content_object
#                         if product and hasattr(product, 'stock'):
#                             product.stock += item.quantity
#                             product.save()

#                     updated_request.order.status = 'RETURNED'
#                     updated_request.order.save()
#                     print("Order status updated to RETURNED")
                    
#             # Trigger email here directly for testing
#             print("Attempting to send confirmation email...")
            
#             return Response({
#                 "message": f"Return request updated to {updated_request.status}",
#                 "data": RefundRequestSerializer(updated_request).data
#             })

#         return Response(serializer.errors, status=400)

