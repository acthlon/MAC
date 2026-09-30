import uuid

from django.db import models
from django.utils import timezone

from accounts.models import CustomUser
from core.choices import (
    PaymentMethodChoice,
    PaymentStatus,
    RefundMethodChoice,
    ReturnStatus,
    Status,
)
from core.models import TimeStampModel, get_refund_evidence_path, get_refund_receipts
from order.models import Order, OrderItem


class PaymentMethod(TimeStampModel):
    id = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False, primary_key=True
    )
    code = models.CharField(
        max_length=50, unique=True, choices=PaymentMethodChoice.choices
    )
    description = models.TextField(blank=True, null=True)
    status = models.CharField(choices=Status.choices, default=Status.ACTIVE)
    display_order = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Payment Methods"
        ordering = [
            "code",
        ]

    def __str__(self):
        return self.code


# Import TimeStamp
# NOTE: Never store card_bins and cvv
class Payment(TimeStampModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    payment_method_code = models.CharField(
        max_length=50,
        choices=PaymentMethodChoice.choices,
        editable=False,
        null=True,
        blank=True,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=4, default="NGN")
    status = models.CharField(
        choices=PaymentStatus.choices, max_length=20, default=PaymentStatus.PENDING
    )

    failure_reason  = models.CharField(max_length=255,blank=True,null=True)

    reference = models.CharField(max_length=100, blank=True, null=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    authorization_code = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.reference} for Order {self.order.id}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Payments"


class ReturnRequest(TimeStampModel):
    return_number = models.CharField(
        max_length=30, unique=True, editable=False, null=True, blank=True
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="return_requests",
        null=False,
        blank=True,
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        related_name="return_requests",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="return_requests",
    )

    reason = models.TextField()
    evidence_image = models.ImageField(
        upload_to=get_refund_evidence_path, null=True, blank=True
    )

    refund_receipt_image = models.ImageField(
        upload_to=get_refund_receipts, null=True, blank=True
    )
    status = models.CharField(
        max_length=20, choices=ReturnStatus.choices, default=ReturnStatus.PENDING
    )
    refund_method = models.CharField(
        max_length=50, choices=RefundMethodChoice.choices, null=True, blank=True
    )

    return_tracking_id = models.CharField(max_length=50, null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    return_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    approved_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @property
    def generate_return_number(self):
        from utils.payments.payment import ReturnUtils  # isort: skip

        return ReturnUtils.generate_return_number(self)

    @property
    def generate_return_tracking_id(self):
        from utils.payments.payment import ReturnUtils  # isort: skip

        return ReturnUtils.generate_return_tracking_id(self)

    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = self.generate_return_number
        if self.id and self.status == ReturnStatus.APPROVED:
            if self.order.payment_method_name == PaymentMethodChoice.CASH_ON_DELIVERY:
                self.refund_method = RefundMethodChoice.BANK_TRANSFER

            elif self.order.payment_method_name == PaymentMethodChoice.PAYSTACK:
                self.refund_method = RefundMethodChoice.PAYSTACK

        if self.status == ReturnStatus.COMPLETED and not self.processed_at:
            self.processed_at = timezone.now()

        if self.status == ReturnStatus.APPROVED:
            if not self.return_tracking_id:
                self.return_tracking_id = self.generate_return_tracking_id

            if not self.approved_at:
                self.approved_at = timezone.now()

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Return Requests"

    def __str__(self):
        return f"Return #{self.return_number} - ({self.status})"
