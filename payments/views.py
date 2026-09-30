import hashlib
import hmac
import json
from functools import partial

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from drf_spectacular.utils import extend_schema
from paystackapi.transaction import Transaction
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from core.choices import (
    OrderStatus,
    PaymentMethodChoice,
    PaymentStatus,
    ReturnStatus,
)
from core.permissions import IsAdminOrReadOnly
from order.models import Order
from payments.models import Payment, PaymentMethod, ReturnRequest
from payments.serializers import (
    InitiatePaymentResponseSerializer,
    InitiatePaymentSerializer,
    PaymentCallbackSerializer,
    ReturnRequestAdminManageSerializer,
    ReturnRequestCreateSerializer,
    ReturnRequestCustomerManageSerializer,
    ReturnRequestDetailSerializer,
    ReturnRequestListSerializer,
    ReturnRequestTrackingSerializer,
)
from payments.tasks import (
    send_admin_stock_shortage_alert_task,
    send_refund_confirmation_email,
)


class InitializePaymentAPIView(generics.GenericAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = InitiatePaymentSerializer

    @extend_schema(
        request=InitiatePaymentSerializer,
        responses={200: InitiatePaymentResponseSerializer},
    )
    def post(self, request, pk):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        order = get_object_or_404(Order, id=pk, status=OrderStatus.CREATED, user=user)

        payment_method = get_object_or_404(
            PaymentMethod, code=serializer.validated_data.get("method_code")
        )

        existing_payment = Payment.objects.filter(
            order=order,
            user=user,
            status__in=[PaymentStatus.INITIALIZED, PaymentStatus.PENDING],
        ).first()

        if existing_payment:
            return Response(
                {"message": "Payment has been initialized for this order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if order.payment_method_name != payment_method.code:
            order.payment_method_name = payment_method.code
            order.save(update_fields=["payment_method_name"])

        payment = Payment.objects.create(
            user=user,
            order=order,
            payment_method_code=payment_method.code,
            amount=order.total_amount,
            currency="NGN",
        )

        if payment.payment_method_code == PaymentMethodChoice.PAYSTACK:
            amount_in_kobo = int(order.total_amount * 100)
            paystack_tx = Transaction(secret_key=settings.PAYSTACK_SECRET_KEY)

            callback_url = reverse("payment_callback", request=request)
            customer_email = (order.shipping_address_snapshot or {}).get(
                "email"
            ) or user.email

            paystack_response = paystack_tx.initialize(
                email=customer_email,
                amount=amount_in_kobo,
                reference=str(payment.id),
                currency="NGN",
                callback_url=callback_url,
                metadata={"order_id": str(order.id), "payment_id": str(payment.id)},
                label=f"Checkout_{order.id}",
            )

            if paystack_response.get("status"):
                reference = paystack_response.get("data", {}).get("reference")

                with transaction.atomic():
                    order.payment_reference = reference
                    payment.reference = reference
                    payment.status = PaymentStatus.INITIALIZED

                    order.save(update_fields=["payment_reference"])
                    payment.save(update_fields=["reference", "status"])

                    return Response(
                        {
                            "authorization_url": paystack_response.get("data", {}).get(
                                "authorization_url"
                            ),
                            "reference": reference,
                        },
                        status=status.HTTP_200_OK,
                    )

            else:
                payment.status = PaymentStatus.FAILED
                payment.save()
                return Response(
                    {"detail": "Payment initialization failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif payment.payment_method_code == PaymentMethodChoice.CASH_ON_DELIVERY:
            with transaction.atomic():
                order.status = OrderStatus.CONFIRMED
                order.save()
                return Response(
                    {
                        "message": "Order placed successfully with Cash on Delivery",
                        "order_id": str(order.id),
                    },
                    status=status.HTTP_200_OK,
                )

        return Response(
            {"error": "Unsupported payment method"}, status=status.HTTP_400_BAD_REQUEST
        )


class PaymentCallbackAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentCallbackSerializer

    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        reference = serializer.validated_data.get("reference")

        payment = get_object_or_404(Payment, reference=reference)

        if payment.status == PaymentStatus.SUCCESSFUL:
            return Response(
                {
                    "message": "Payment successful — order confirmed!",
                    "status": payment.status,
                    "reference": payment.reference,
                },
                status=status.HTTP_200_OK,
            )
        elif payment.status == PaymentStatus.FAILED:
            return Response(
                {
                    "message": "Payment failed — please try again",
                    "status": payment.status,
                    "reference": payment.reference,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif payment.status == PaymentStatus.PENDING:
            return Response(
                {
                    "message": "Payment pending — we'll notify you soon",
                    "status": payment.status,
                    "reference": payment.reference,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "Payment status unknown", "status": payment.status},
            status=status.HTTP_200_OK,
        )


class PaymentCallbackHTMLView(View):
    def get(self, request):
        reference = request.GET.get("reference")
        payment = get_object_or_404(Payment, reference=reference)

        # Default to the database status
        html_status = str(payment.status).lower()

        if payment.status in [PaymentStatus.INITIALIZED, PaymentStatus.PENDING]:
            try:
                paystack_tx = Transaction(secret_key=settings.PAYSTACK_SECRET_KEY)
                response = paystack_tx.verify(reference=reference)

                if response and response.get("status"):
                    paystack_status = response.get("data", {}).get("status")
                    if paystack_status == "success":
                        html_status = "successful"
                    elif paystack_status in ["failed", "abandoned"]:
                        html_status = "failed"
                    else:
                        html_status = "pending"
            except Exception:
                pass  # Fallback to displaying the current DB status

        if html_status == "initialized":
            html_status = "pending"

        context = {
            "status": html_status,
            "reference": payment.reference,
            "order_number": payment.order.order_number
            if hasattr(payment.order, "order_number")
            else payment.order.id,
        }
        return render(request, "payments/callback.html", context)


@require_POST
@csrf_exempt
def paystack_webhook(request):

    # Verify Paystack signature
    request_body = request.body
    secret = settings.PAYSTACK_SECRET_KEY.encode()
    signature = request.headers.get("x-paystack-signature")

    if not signature:
        return HttpResponse(status=400)

    expected_signature = hmac.new(secret, request_body, hashlib.sha512).hexdigest()

    if signature != expected_signature:
        return HttpResponse(status=400)

    # Parse the webhook data
    try:
        post_response = json.loads(request_body)

    except json.JSONDecodeError:
        return HttpResponse(status=400)

    # all the aove are stll security check below is the processing of the real handling of successful payment
    if post_response["event"] == "charge.success":
        data = post_response["data"]
        reference = data.get("reference")
        authorization = data.get("authorization", {})

        card_brand = authorization.get("brand")
        card_last4 = authorization.get("last4")
        auth_code = authorization.get("authorization_code")

        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(reference=reference)
            except Payment.DoesNotExist:
                return HttpResponse(status=200)

            # Prevent processing the same payment multiple times
            if payment.status != PaymentStatus.SUCCESSFUL:
                payment.status = PaymentStatus.SUCCESSFUL
                payment.processed_at = timezone.now()
                payment.paid_at = timezone.now()
                payment.card_brand = card_brand
                payment.card_last4 = card_last4
                payment.authorization_code = auth_code
                payment.save()

                order = payment.order

                stock_shortage = False
                # Deduct stock from products using row locking
                for order_item in order.items.select_related("content_type").all():
                    ModelClass = order_item.content_type.model_class()

                    # 1. Fetch and lock the specific variant/item row
                    locked_item = ModelClass.objects.select_for_update().get(
                        pk=order_item.object_id
                    )

                    # 2. Check stock on the freshly locked object and update
                    if hasattr(locked_item, "stock"):
                        if locked_item.stock >= order_item.quantity:
                            locked_item.stock -= order_item.quantity
                        else:
                            stock_shortage = True
                            locked_item.stock = 0

                        locked_item.save(update_fields=["stock"])

                # Update order status - This is the most important part

                if stock_shortage:
                    order.admin_notes = (
                        "STOCK SHORTAGE: Item was out of stock when payment was confirmed. "
                        "Admin needs to procure item immediately to meet delivery timeframe."
                    )
                    transaction.on_commit(
                        partial(send_admin_stock_shortage_alert_task.delay, order.id)
                    )
                order.status = OrderStatus.CONFIRMED
                order.payment_status = PaymentStatus.SUCCESSFUL
                order.payment_reference = payment.reference
                order.save()

    elif post_response["event"] == "charge.failed":
        data = post_response["data"]
        reference = data.get("reference")
        failure_message = (
            data.get("gateway_response") or data.get("message") or "Payment failed"
        )

        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(reference=reference)
                if payment.status != PaymentStatus.FAILED:
                    payment.status = PaymentStatus.FAILED
                    payment.failure_reason = failure_message
                    payment.processed_at = timezone.now()

                    payment.save()
            except Payment.DoesNotExist:
                pass

    elif post_response["event"] == "refund.processed":
        data = post_response["data"]

        # Paystack includes the original transaction reference in the refund data
        transaction_reference = data.get("transaction", {}).get("reference")
        if not transaction_reference:
            transaction_reference = data.get("transaction_reference")

        with transaction.atomic():
            try:
                return_request = ReturnRequest.objects.select_for_update().get(
                    order__payment_reference=transaction_reference,
                    status__in=[ReturnStatus.APPROVED, ReturnStatus.PROCESSING],
                )

                return_request.status = ReturnStatus.COMPLETED
                return_request.completed_at = timezone.now()
                return_request.save()

                transaction.on_commit(
                    partial(
                        send_refund_confirmation_email.delay,
                        return_request.id,
                        return_request.user.id,
                    )
                )

            except ReturnRequest.DoesNotExist:
                pass

    elif post_response["event"] == "refund.failed":
        data = post_response["data"]
        transaction_reference = data.get("transaction", {}).get(
            "reference"
        ) or data.get("transaction_reference")

        with transaction.atomic():
            try:
                return_request = ReturnRequest.objects.select_for_update().get(
                    order__payment_reference=transaction_reference,
                    status__in=[ReturnStatus.APPROVED, ReturnStatus.PROCESSING],
                )

                # Log the failure so the Admin can manually check it
                return_request.admin_notes = f"Paystack automatic refund failed: {data.get('message', 'Unknown error')}"
                return_request.save()
            except ReturnRequest.DoesNotExist:
                pass

    return HttpResponse(status=200)


class CreateReturnRequestAPIView(generics.CreateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = ReturnRequestCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        request = self.request
        user = request.user
        order_number = self.kwargs.get("order_number")

        order = get_object_or_404(Order, order_number=order_number, user=user)

        context["order"] = order
        return context


class ReturnRequestListAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReturnRequestListSerializer

    def get(self, request, *args, **kwargs):

        user = self.request.user

        single_item_return_request = ReturnRequest.objects.filter(
            order_item__isnull=False, user=user
        ).order_by("-created_at")
        full_order_return_request = (
            ReturnRequest.objects.filter(order_item__isnull=True, user=user)
            .prefetch_related("order__items")
            .order_by("-created_at")
        )

        data = {
            "single_item_return_request": single_item_return_request,
            "full_order_return_request": full_order_return_request,
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)


class ReturnRequestDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = ReturnRequestDetailSerializer

    def get_object(self):
        return_number = self.kwargs.get("return_number")
        user = self.request.user
        if user.is_staff:
            return get_object_or_404(ReturnRequest, return_number=return_number)
        return get_object_or_404(ReturnRequest, return_number=return_number, user=user)


# CUSTOMER
class ReturnRequestCustomerManageAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReturnRequestCustomerManageSerializer

    def get_object(self):
        # Ensure customers can ONLY see/edit/delete their OWN return requests
        user = self.request.user
        return_id = self.kwargs.get("return_id")

        return_request = get_object_or_404(ReturnRequest, user=user, id=return_id)
        return return_request

    def perform_destroy(self, instance):
        if instance.status != ReturnStatus.PENDING:
            raise serializers.ValidationError(
                {
                    "message": "You cannot cancel/delete a return request that is already processed."
                }
            )
        instance.delete()


class ReturnRequestAdminManageAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [
        IsAdminOrReadOnly,
    ]
    serializer_class = ReturnRequestAdminManageSerializer

    http_method_names = ["patch", "delete", "options"]

    def get_object(self):

        return_id = self.kwargs.get("return_id")
        return_request = get_object_or_404(ReturnRequest, id=return_id)

        return return_request


class ReturnRequestTrackingAPIView(generics.RetrieveAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = ReturnRequestTrackingSerializer

    def get_object(self):

        user = self.request.user
        return_number = self.kwargs.get("return_number")
        tracking_id = self.kwargs.get("tracking_id")
        return_request = get_object_or_404(
            ReturnRequest,
            return_number=return_number,
            user=user,
            return_tracking_id=tracking_id,
        )

        return return_request
