from core.choices import PaymentMethodChoice
from payments.processors.base import BasePaymentProcessor
from payments.processors.cash_on_delivery import CashOnDeliveryProcessor
from payments.processors.paystack import PaystackPaymentProcessor


class PaymentRegistry:
    _HANDLERS: dict[str, BasePaymentProcessor] = {
        PaymentMethodChoice.PAYSTACK: PaystackPaymentProcessor(),
        PaymentMethodChoice.CASH_ON_DELIVERY: CashOnDeliveryProcessor(),
    }

    @classmethod
    def get_payment_processor(cls, method_code: str) -> BasePaymentProcessor:
        processor = cls._HANDLERS.get(method_code)
        if not processor:
            raise ValueError(f"Unsupported payment method code: '{method_code}'")
        return processor
