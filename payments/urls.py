from django.urls import path
from payments.views import initializePaymentAPIView,PaymentCallbackAPIView,paystack_webhook


urlpatterns = [
    path('<uuid:pk>/initialize/',initializePaymentAPIView.as_view(),name='initialize-payment'),
    path('callback/',PaymentCallbackAPIView.as_view(),name='payment-callback'),
    path('webhook/paystack/', paystack_webhook, name='paystack-webhook')
]