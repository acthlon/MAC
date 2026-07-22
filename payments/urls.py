from django.urls import path

from payments.views import (CreateRefundRequestAPIView, PaymentCallbackAPIView,
                            ReturnRequestActionAPIView,
                            initializePaymentAPIView, paystack_webhook)

urlpatterns = [
    path('<uuid:pk>/initialize/',initializePaymentAPIView.as_view(),name='initialize_payment'),
    path('callback/',PaymentCallbackAPIView.as_view(),name='payment_callback'),
    path('webhook/paystack/',paystack_webhook, name='paystack_webhook'),
    path('refund/<uuid:order_id>/create/',CreateRefundRequestAPIView.as_view(),name="create_refund_request"),
    path('refund/<str:return_id>/update/',ReturnRequestActionAPIView.as_view(),name='return_request_action')
]