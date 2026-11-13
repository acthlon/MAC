from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PaymentContext:
    # mandatory fields
    amount: Decimal
    customer_email: str
    reference: str
    metadata: dict

    # optional fiels
    currency: str = "NGN"
    callback_url: str = ""
    label: str = ""


class BasePaymentProcessor(ABC):
    @abstractmethod
    def get_display_name(self) -> str:
        pass

    @abstractmethod
    def initialize(self, context: PaymentContext) -> dict:
        pass
