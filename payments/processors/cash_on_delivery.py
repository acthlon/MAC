from django.db import transaction

from core.choices import OrderStatus, PaymentStatus
from payments.processors.base import BasePaymentProcessor, PaymentContext


class CashOnDeliveryProcessor(BasePaymentProcessor):
    def get_display_name(self) -> str:
        return "Cash on Delivery"

    def initialize(self, _context: PaymentContext, order, payment) -> dict:

        with transaction.atomic():
            order.status = OrderStatus.CONFIRMED
            order.save(update_fields=["status"])

            payment.status = PaymentStatus.PENDING
            payment.save(update_fields=["status"])

        return {
            "success": True,
            "data": {
                "message": "Order placed successfully with Cash on Delivery",
                "order_id": str(order.id),
            },
        }
