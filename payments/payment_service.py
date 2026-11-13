from payments.processors.base import PaymentContext
from payments.processors.registry import PaymentRegistry


class PaymentService:
    def initialize_payment(
        self, method_code: str, context: PaymentContext, order, payment
    ) -> dict:
        processor = PaymentRegistry.get_payment_processor(method_code)

        return processor.initialize(context=context, order=order, payment=payment)
