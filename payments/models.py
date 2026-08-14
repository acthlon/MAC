import uuid

from django.db import models

from accounts.models import CustomUser
from core.choices import PaymentStatus, RefundStatus  # NOTE: Do not reassign  NOT
from order.models import Order, PaymentMethod


# Import TimeStamp
class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT, related_name="user_payments"
    )
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="order_payments"
    )
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=4, default="NGN")
    status = models.CharField(
        choices=PaymentStatus.choices, max_length=20, default=PaymentStatus.PENDING
    )
    reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_bin = models.CharField(
        max_length=6, blank=True, null=True
    )  # NOTE: Never store card_bins and cvv
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    authorization_code = models.CharField(max_length=100, blank=True, null=True)

    # NOTE: this method is not really needed here
    @property
    def masked_card(self):
        """Returns something like: 408408******4081"""
        if self.card_brand and self.card_last4:
            return f"{self.card_brand}******{self.card_last4}"
        return "N/A"

    def __str__(self):
        return f"Payment {self.reference} for Order {self.order.id}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Payments"


# NOTE: use timestamp here
class RefundRequest(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="return_requests"
    )
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    reason = models.TextField()
    status = models.CharField(
        max_length=20, choices=RefundStatus.choices, default=RefundStatus.PENDING
    )  # NOTE: Adjust here too
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)

    refund_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ["-requested_at"]
        verbose_name_plural = "Return Requests"

    def __str__(self):
        return f"Return #{self.id} - Order #{self.order.id} ({self.status})"
