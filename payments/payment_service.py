from decimal import Decimal
from typing import Any

from django.db.models import Sum

from core.choices import PaymentStatus
from order.models import Order
from payments.models import Payment
from payments.processors.base import PaymentContext
from payments.processors.registry import PaymentRegistry


class PaymentService:
    def initialize_payment(
        self,
        method_code: str,
        context: PaymentContext,
        order: Order,
        payment: Payment,
    ) -> dict[str, Any]:
        processor = PaymentRegistry.get_payment_processor(method_code)
        return processor.initialize(context=context, order=order, payment=payment)

    @staticmethod
    def get_remaining_order_balance(order: Order) -> Decimal:

        total_paid: Decimal = Payment.objects.filter(
            order=order,
            status__in=[PaymentStatus.SUCCESSFUL, PaymentStatus.UNDERPAID],
        ).aggregate(total=Sum("amount_paid", default=Decimal("0.00")))["total"]
        difference_amount = max(order.total_amount - total_paid, Decimal("0.00"))
        print(difference_amount)
        return difference_amount

    @staticmethod
    def _resolve_customer_email(order: Order, user: Any) -> str:
        snapshot_email = (order.shipping_address_snapshot or {}).get("email")
        return snapshot_email or getattr(user, "email", "")

    def _create_and_dispatch(
        self,
        *,
        order: Order,
        user: Any,
        method_code: str,
        amount: Decimal,
        currency: str,
        callback_url: str,
        payment_reason: str,
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if amount <= Decimal("0.00"):
            return {
                "success": False,
                "data": {"detail": "No remaining balance due for this order."},
            }

        if order.payment_method_name != method_code:
            order.payment_method_name = method_code
            order.save(update_fields=["payment_method_name"])

        payment = Payment.objects.create(
            user=user,
            order=order,
            payment_method_code=method_code,
            amount=amount,
            amount_paid=Decimal("0.00"),
            currency=currency,
            payment_reason=payment_reason,
        )

        metadata: dict[str, Any] = {
            "order_id": str(order.id),
            "payment_id": str(payment.id),
            **(extra_metadata or {}),
        }

        context = PaymentContext(
            amount=amount,
            customer_email=self._resolve_customer_email(order, user),
            reference=str(payment.id),
            callback_url=callback_url,
            currency=currency,
            metadata=metadata,
        )

        return self.initialize_payment(
            method_code=method_code,
            context=context,
            order=order,
            payment=payment,
        )

    def create_and_initialize_order_payment(
        self,
        *,
        order: Order,
        user: Any,
        method_code: str,
        callback_url: str,
        currency: str = "NGN",
    ) -> dict[str, Any]:

        amount_due = self.get_remaining_order_balance(order)
        is_balance = amount_due < order.total_amount

        return self._create_and_dispatch(
            order=order,
            user=user,
            method_code=method_code,
            amount=amount_due,
            currency=currency,
            callback_url=callback_url,
            payment_reason=(
                "Balance settlement for underpayment"
                if is_balance
                else "Initial order payment"
            ),
            extra_metadata={"is_balance_payment": is_balance},
        )

    def create_and_initialize_underpayment(
        self,
        *,
        order: Order,
        original_payment: Payment,
        callback_url: str,
    ) -> dict[str, Any]:

        amount_due = self.get_remaining_order_balance(order)
        method_code = original_payment.payment_method_code or order.payment_method_name

        return self._create_and_dispatch(
            order=order,
            user=original_payment.user or order.user,
            method_code=method_code,
            amount=amount_due,
            currency=original_payment.currency or "NGN",
            callback_url=callback_url,
            payment_reason="Balance settlement for underpayment",
            extra_metadata={
                "is_balance_payment": True,
                "parent_payment_id": str(original_payment.id),
            },
        )
