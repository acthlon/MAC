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


class PaymentCallbackAPIView(APIView):
    
    permission_classes = [IsAuthenticated,] 
    
    def get(self, request):
    
        reference = request.query_params.get('reference')
        payment = get_object_or_404(Payment, reference=reference)
        transaction = Transaction(secret_key=settings.PAYSTACK_SECRET_KEY)
        response = transaction.verify(reference=reference)

        if response['status'] and response['data']['status'] == 'success':
            payment.status = 'SUCCESSFUL'
            payment.save()
            payment.order.status = 'CONFIRMED'
            payment.order.save()
            return Response({"message": "Payment successful",'response':response})
        else:
            payment.status = 'FAILED'
            payment.save()
            return Response({"message": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)