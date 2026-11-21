import hashlib
import hmac
import json
import logging
from decimal import Decimal
from functools import partial

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
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
    PaymentStatus,
    ReturnStatus,
)
from core.permissions import IsAdminOrReadOnly
from order.models import Order
from payments.models import Payment, PaymentMethod, ReturnRequest
from payments.payment_service import PaymentService
from payments.processors.base import PaymentContext
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
    send_payment_discrepancy_notification_task,
    send_refund_confirmation_email,
)
from payments.tokens import verify_underpayment_token


class InitializePaymentAPIView(generics.GenericAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = InitiatePaymentSerializer

    payment_service = PaymentService()

    @extend_schema(
        request=InitiatePaymentSerializer,
        responses={200: InitiatePaymentResponseSerializer},
    )
    def post(self, request, pk):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        order = get_object_or_404(
            Order,
            id=pk,
            status__in=[OrderStatus.CREATED, OrderStatus.ON_HOLD],
            user=user,
        )

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

        callback_url = reverse("payment_callback", request=request)
        customer_email = (order.shipping_address_snapshot or {}).get(
            "email"
        ) or user.email

        context = PaymentContext(
            amount=order.total_amount,
            customer_email=customer_email,
            reference=str(payment.id),
            callback_url=callback_url,
            metadata={
                "order_id": str(order.id),
                "payment_id": str(payment.id),
            },
        )

        try:
            result = self.payment_service.initialize_payment(
                method_code=payment_method.code,
                context=context,
                payment=payment,
                order=order,
            )
        except Exception as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if result["success"]:
            return Response(result["data"], status=status.HTTP_200_OK)

        return Response(result["data"], status=status.HTTP_400_BAD_REQUEST)


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


logger = logging.getLogger("payments.webhook")


@require_POST
@csrf_exempt
def paystack_webhook(request):

    signature = request.headers.get("x-paystack-signature")

    if not signature:
        logger.warning(
            "[PAYSTACK WEBHOOK] Rejected: Missing 'x-paystack-signature' header."
        )
        return HttpResponse(status=400)

    secret_key = getattr(settings, "PAYSTACK_SECRET_KEY", "").strip()

    if not secret_key:
        logger.critical(
            "[PAYSTACK WEBHOOK] Server Configuration Error: PAYSTACK_SECRET_KEY is empty."
        )
        return HttpResponse(status=500)

    payload_bytes = request.body

    expected_signature = hmac.new(
        secret_key.encode("utf-8"), payload_bytes, hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        logger.warning("[PAYSTACK WEBHOOK] Rejected: Cryptographic signature mismatch.")
        return HttpResponse(status=400)

    try:
        event_data = json.loads(payload_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error(f"[PAYSTACK WEBHOOK] JSON Decode Failure: {exc}")
        return HttpResponse(status=400)

    event_type = event_data.get("event")
    data = event_data.get("data", {})
    reference = data.get("reference")

    logger.info(
        f"[PAYSTACK WEBHOOK] Processing event '{event_type}' for reference: {reference}"
    )

    if event_type == "charge.success":
        paid_amount_kobo = data.get("amount", 0)
        paid_naira = Decimal(paid_amount_kobo) / Decimal(100)

        authorization = data.get("authorization") or {}
        card_brand = authorization.get("brand")
        card_last4 = authorization.get("last4")
        auth_code = authorization.get("authorization_code")

        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(reference=reference)
            except Payment.DoesNotExist:
                logger.error(
                    f"[PAYSTACK WEBHOOK] Payment with reference {reference} not found in database."
                )
                return HttpResponse(status=200)

            # Idempotency Guard
            if payment.status == PaymentStatus.SUCCESSFUL:
                logger.info(
                    f"[PAYSTACK WEBHOOK] Idempotency: Payment {reference} is already processed."
                )
                return HttpResponse(status=200)

            order = payment.order
            expected_amount_kobo = int(payment.amount * 100)
            difference_kobo = paid_amount_kobo - expected_amount_kobo

            # CASE 1: UNDERPAYMENT (Deficit Settlement)
            if difference_kobo < 0:
                shortage_naira = abs(Decimal(difference_kobo) / Decimal(100))
                logger.warning(
                    f"[LEDGER UNDERPAYMENT] Ref: {reference}. "
                    f"Expected: ₦{payment.amount}, Received: ₦{paid_naira}, Shortage: ₦{shortage_naira}"
                )

                payment.status = PaymentStatus.UNDERPAID
                payment.amount_paid = paid_naira
                payment.difference_amount = shortage_naira
                payment.payment_reason = (
                    f"Partial Payment: Shortage of ₦{shortage_naira:,.2f}"
                )
                payment.card_brand = card_brand
                payment.card_last4 = card_last4
                payment.authorization_code = auth_code
                payment.save(
                    update_fields=[
                        "status",
                        "amount_paid",
                        "difference_amount",
                        "payment_reason",
                        "card_brand",
                        "card_last4",
                        "authorization_code",
                    ]
                )

                order.status = OrderStatus.ON_HOLD
                order.payment_reference = payment.reference
                order.admin_notes = f"PAYMENT SHORTAGE: ₦{shortage_naira:,.2f} required to release order."
                order.save(update_fields=["status", "payment_reference", "admin_notes"])

                if payment.user:
                    transaction.on_commit(
                        partial(
                            send_payment_discrepancy_notification_task.delay,
                            str(payment.id),
                            str(payment.user.id),
                        )
                    )
                return HttpResponse(status=200)

            # CASE 2 & 3: FULL PAYMENT OR OVERPAYMENT

            payment.status = PaymentStatus.SUCCESSFUL
            payment.amount_paid = paid_naira
            payment.processed_at = timezone.now()
            payment.paid_at = timezone.now()
            payment.card_brand = card_brand
            payment.card_last4 = card_last4
            payment.authorization_code = auth_code

            is_overpayment = difference_kobo > 0
            if is_overpayment:
                excess_naira = Decimal(difference_kobo) / Decimal(100)
                payment.difference_amount = excess_naira
                payment.payment_reason = (
                    f"Full Payment with Excess: Overpaid ₦{excess_naira:,.2f}"
                )
                logger.info(
                    f"[LEDGER OVERPAYMENT] Ref: {reference}. Excess: ₦{excess_naira}"
                )
            else:
                payment.difference_amount = Decimal("0.00")
                payment.payment_reason = "Full Payment Confirmed"

            payment.save(
                update_fields=[
                    "status",
                    "amount_paid",
                    "difference_amount",
                    "payment_reason",
                    "processed_at",
                    "paid_at",
                    "card_brand",
                    "card_last4",
                    "authorization_code",
                ]
            )

            # Deduct stock safely with sorted row locks
            stock_shortage = False
            ordered_items = (
                order.items.select_related("content_type")
                .order_by("content_type_id", "object_id")
                .all()
            )

            for order_item in ordered_items:
                model_class = order_item.content_type.model_class()
                locked_item = model_class.objects.select_for_update().get(
                    pk=order_item.object_id
                )

                if hasattr(locked_item, "stock"):
                    if locked_item.stock >= order_item.quantity:
                        locked_item.stock -= order_item.quantity
                    else:
                        stock_shortage = True
                        locked_item.stock = 0
                    locked_item.save(update_fields=["stock"])

            if stock_shortage:
                order.admin_notes = (
                    "STOCK SHORTAGE: Item was out of stock when payment was confirmed. "
                    "Admin procurement required."
                )
                transaction.on_commit(
                    partial(send_admin_stock_shortage_alert_task.delay, order.id)
                )

            order.status = OrderStatus.CONFIRMED
            order.payment_status = PaymentStatus.SUCCESSFUL
            order.payment_reference = payment.reference
            order.save(
                update_fields=[
                    "status",
                    "payment_status",
                    "payment_reference",
                    "admin_notes",
                ]
            )

            # If overpaid, queue alert post-commit
            if is_overpayment and payment.user:
                transaction.on_commit(
                    partial(
                        send_payment_discrepancy_notification_task.delay,
                        str(payment.id),
                        str(payment.user.id),
                    )
                )

            return HttpResponse(status=200)

    elif event_type == "charge.failed":
        failure_message = (
            data.get("gateway_response")
            or data.get("message")
            or "Payment authorization failed"
        )
        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(reference=reference)
                if payment.status != PaymentStatus.FAILED:
                    payment.status = PaymentStatus.FAILED
                    payment.failure_reason = failure_message
                    payment.processed_at = timezone.now()
                    payment.save(
                        update_fields=["status", "failure_reason", "processed_at"]
                    )
            except Payment.DoesNotExist:
                pass
        return HttpResponse(status=200)

    elif event_type == "refund.processed":
        tx_reference = data.get("transaction", {}).get("reference") or data.get(
            "transaction_reference"
        )
        with transaction.atomic():
            try:
                return_request = ReturnRequest.objects.select_for_update().get(
                    order__payment_reference=tx_reference,
                    status__in=[ReturnStatus.APPROVED, ReturnStatus.PROCESSING],
                )
                return_request.status = ReturnStatus.COMPLETED
                return_request.completed_at = timezone.now()
                return_request.save(update_fields=["status", "completed_at"])

                transaction.on_commit(
                    partial(
                        send_refund_confirmation_email.delay,
                        return_request.id,
                        return_request.user.id,
                    )
                )
            except ReturnRequest.DoesNotExist:
                pass
        return HttpResponse(status=200)

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


class ResolveUnderpaymentRedirectView(View):
    payment_service = PaymentService()

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        frontend_url = settings.FRONTEND_URL.rstrip("/")

        # 1. Authenticate via signed token instead of request.user
        try:
            payment_id, user_id = verify_underpayment_token(token)
        except (BadSignature, SignatureExpired, KeyError):
            return HttpResponseRedirect(
                f"{frontend_url}/orders?error=invalid_or_expired_link"
            )

        with transaction.atomic():
            try:
                payment = (
                    Payment.objects.select_for_update()
                    .select_related("order", "user")
                    .get(id=payment_id, user_id=user_id)
                )
            except Payment.DoesNotExist:
                return HttpResponseRedirect(
                    f"{frontend_url}/orders?error=payment_not_found"
                )
            order = payment.order

            balance_due = self.payment_service.get_remaining_order_balance(order)
            if balance_due <= Decimal("0.00") or order.status != OrderStatus.ON_HOLD:
                return HttpResponseRedirect(
                    f"{frontend_url}/orders/{order.id}?status=already_paid"
                )

            callback_url = f"{settings.SITE_URL}/payment-callback"

            result = self.payment_service.create_and_initialize_underpayment(
                order=order,
                original_payment=payment,
                callback_url=callback_url,
            )

        if result.get("success") and result.get("data", {}).get("authorization_url"):
            return HttpResponseRedirect(result["data"]["authorization_url"])

        if (
            result.get("data", {}).get("detail")
            == "No remaining balance due for this order."
        ):
            return HttpResponseRedirect(
                f"{frontend_url}/orders/{order.id}?status=already_paid"
            )

        return HttpResponseRedirect(
            f"{frontend_url}/orders/{order.id}?error=gateway_unavailable"
        )
