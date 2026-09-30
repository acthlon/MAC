from django.urls import path

from payments.views import (
    CreateReturnRequestAPIView,
    InitializePaymentAPIView,
    PaymentCallbackAPIView,
    PaymentCallbackHTMLView,
    ReturnRequestAdminManageAPIView,
    ReturnRequestCustomerManageAPIView,
    ReturnRequestDetailAPIView,
    ReturnRequestListAPIView,
    ReturnRequestTrackingAPIView,
    paystack_webhook,
)

urlpatterns = [
    path(
        "<uuid:pk>/initialize/",
        InitializePaymentAPIView.as_view(),
        name="initialize_payment",
    ),
    path(
        "callback/api/", PaymentCallbackAPIView.as_view(), name="payment_callback_api"
    ),
    path("callback/", PaymentCallbackHTMLView.as_view(), name="payment_callback"),
    path("webhook/paystack/", paystack_webhook, name="paystack_webhook"),
    path(
        "return/<str:order_number>/create/",
        CreateReturnRequestAPIView.as_view(),
        name="create_return_request",
    ),
    path(
        "return/details/<str:return_number>/",
        ReturnRequestDetailAPIView.as_view(),
        name="return_request_details",
    ),
    path("return/", ReturnRequestListAPIView.as_view(), name="return_list"),
    path(
        "customer/return/<str:return_id>/manage/",
        ReturnRequestCustomerManageAPIView.as_view(),
        name="return_manage_customer",
    ),
    path(
        "admin/return/<str:return_id>/manage/",
        ReturnRequestAdminManageAPIView.as_view(),
        name="return_manage_admin",
    ),
    path(
        "return/<str:return_number>/<str:tracking_id>/",
        ReturnRequestTrackingAPIView.as_view(),
        name="return_tracking",
    ),
]
