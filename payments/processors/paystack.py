from django.conf import settings
from django.db import transaction
from paystackapi.transaction import Transaction as PaystackAPI

from core.choices import PaymentStatus
from payments.processors.base import BasePaymentProcessor, PaymentContext


class PaystackPaymentProcessor(BasePaymentProcessor):
    def get_display_name(self) -> str:
        return "Paystack"

    def initialize(self, context: PaymentContext, order, payment) -> dict:

        amount_in_kobo = int(context.amount * 100)
        paystack_tx = PaystackAPI(secret_key=settings.PAYSTACK_SECRET_KEY)

        try:
            paystack_response = paystack_tx.initialize(
                email=context.customer_email,
                amount=amount_in_kobo,
                reference=context.reference,
                currency=context.currency,
                callback_url=context.callback_url,
                metadata=context.metadata,
                label=context.label or f"Checkout_{context.reference}",
            )
        except Exception as exc:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = f"Network/SDK error: {exc!s}"
            payment.save(update_fields=["status", "failure_reason"])
            return {
                "success": False,
                "data": {"detail": f"Gateway error: {payment.failure_reason}"},
            }

        if paystack_response and paystack_response.get("status"):
            data = paystack_response.get("data", {})
            reference = data.get("reference")

            with transaction.atomic():
                order.payment_reference = reference
                payment.reference = reference
                payment.status = PaymentStatus.INITIALIZED

                order.save(update_fields=["payment_reference"])
                payment.save(update_fields=["reference", "status"])

            return {
                "success": True,
                "data": {
                    "authorization_url": data.get("authorization_url"),
                    "reference": reference,
                },
            }

        rejection_msg = (
            paystack_response.get("message")
            if isinstance(paystack_response, dict)
            else "Paystack rejected transaction"
        )
        payment.status = PaymentStatus.FAILED
        payment.failure_reason = rejection_msg
        payment.save(update_fields=["status", "failure_reason"])

        return {"success": False, "data": {"detail": rejection_msg}}
