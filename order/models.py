import uuid
from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from accounts.models import CustomUser
from core.choices import (
    BOOLEAN_CHOICES,
    AddressType,
    DeliveryStatus,
    DeliveryType,
    OrderStatus,
    PaymentStatus,
    Status,
)
from core.models import TimeStampModel


class Address(TimeStampModel):
    id = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False, primary_key=True
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="delivery_address"
    )
    phone_number = PhoneNumberField()
    alternative_phone_number = PhoneNumberField(blank=True, null=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    delivery_address = models.CharField(max_length=200)
    email = models.EmailField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Nigeria")
    additional_info = models.TextField(max_length=500, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    address_type = models.CharField(choices=AddressType.choices, default="HOME")
    is_selected = models.BooleanField(choices=BOOLEAN_CHOICES, default=False)

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(
                id=self.id
            ).update(is_default=False)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Addresses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.delivery_address}, {self.city}"


class DeliveryMethod(models.Model):
    name = models.CharField(max_length=255, choices=DeliveryType.choices)
    description = models.CharField(max_length=255, null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    estimated_date = models.CharField(max_length=100, null=True, blank=True)
    display_order = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=50, choices=Status.choices, default=Status.ACTIVE
    )
    is_selected = models.BooleanField(choices=BOOLEAN_CHOICES, default=False)

    @property
    def delivery_day(self):
        from utils.orders.order import DeliveryMethodUtils  # isort: skip

        return DeliveryMethodUtils().delivery_day(self)

    def save(self, *args, **kwargs):

        self.estimated_date = self.delivery_day
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Delivery Methods"


class Order(TimeStampModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status
        self._original_delivery_status = self.delivery_status

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name="order")
    order_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    shipping_address_snapshot = models.JSONField(null=True, blank=True)
    delivery_method_name = models.CharField(max_length=200, null=True, blank=True)
    payment_method_name = models.CharField(max_length=200, null=True, blank=True)
    # shipping_address = models.ForeignKey(
    #     Address,
    #     on_delete=models.PROTECT,
    #     related_name="orders",
    #     null=True,
    #     blank=True,
    # )
    total_items = models.IntegerField(default=0, editable=False)
    # delivery_method = models.ForeignKey(
    #     DeliveryMethod,
    #     on_delete=models.PROTECT,
    #     related_name="orders",
    #     null=True,
    #     blank=True,
    # )

    status = models.CharField(
        max_length=30, choices=OrderStatus.choices, default=OrderStatus.CREATED
    )

    # payment_method = models.ForeignKey(
    #     PaymentMethod,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     related_name="order_payment",
    # )

    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(
        max_length=50, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    delivery_status = models.CharField(
        max_length=40, default=DeliveryStatus.PENDING, choices=DeliveryStatus.choices
    )
    tracking_id = models.CharField(max_length=50, null=True, blank=True)
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )
    sub_total_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )

    shipping_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )
    total_discount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )
    currency = models.CharField(max_length=5, default="NGN")
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    out_for_delivery_at = models.DateTimeField(null=True, blank=True)
    failed_delivery_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    customer_note = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)

    @property
    def calculate_total_items(self):

        from utils.orders.order import OrderUtils  # isort: skip

        return OrderUtils.calculate_total_items(self)

    @property
    def calculate_sub_total_amount(self):

        from utils.orders.order import OrderUtils  # isort: skip

        return OrderUtils.calculate_sub_total_amount(self)

    @property
    def calculate_total_discount_amount(self):

        from utils.orders.order import OrderUtils  # isort: skip

        return OrderUtils.calculate_total_discount_amount(self)

    @property
    def calculate_total_amount(self):

        from utils.orders.order import OrderUtils  # isort: skip

        return OrderUtils.calculate_total_amount(self)

    @property
    def get_ordered_day(self):
        from utils.orders.order import OrderUtils  # isort: skip

        return OrderUtils.get_ordered_day(self)

    @property
    def get_delivered_day(self):
        from utils.orders.order import OrderUtils  # isort: skip

        return OrderUtils.get_delivered_day(self)

    def save(self, *args, **kwargs):
        from utils.orders.order import OrderUtils  # isort: skip

        if self.id:
            self.total_amount = self.calculate_total_amount
            self.total_items = self.calculate_total_items
            self.sub_total_amount = self.calculate_sub_total_amount
            self.total_discount = self.calculate_total_discount_amount

        if not self.order_number:
            self.order_number = OrderUtils.generate_order_number(self)

        if self.delivery_status == DeliveryStatus.DELIVERED:
            self.status = OrderStatus.COMPLETED

        if self.delivery_status == DeliveryStatus.CANCELED:
            self.status = OrderStatus.CANCELED

        if (
            self.status == OrderStatus.COMPLETED
            and self.delivery_status == DeliveryStatus.DELIVERED
            and not self.delivered_at
        ):
            self.delivered_at = timezone.now()
        if (
            self.status == OrderStatus.CANCELED
            or self.delivery_status == DeliveryStatus.CANCELED
        ) and not self.canceled_at:
            self.canceled_at = timezone.now()

        if self.status == OrderStatus.CONFIRMED:
            if not self.tracking_id:
                self.tracking_id = OrderUtils.generate_tracking_id(self)

            if self.delivery_status == DeliveryStatus.SHIPPED and not self.shipped_at:
                self.shipped_at = timezone.now()

            if (
                self.delivery_status == DeliveryStatus.OUT_FOR_DELIVERY
                and not self.out_for_delivery_at
            ):
                self.out_for_delivery_at = timezone.now()

            if (
                self.delivery_status == DeliveryStatus.FAILED_DELIVERY
                and not self.failed_delivery_at
            ):
                self.failed_delivery_at = timezone.now()

        super().save(*args, **kwargs)
        self._original_status = self.status
        self._original_delivery_status = self.delivery_status

    class Meta:
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")

    image = models.ImageField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    @property
    def calculate_sub_total(self):
        from utils.orders.order import OrderItemUtils  # isort: skip

        return OrderItemUtils.calculate_sub_total(self)

    @property
    def calculate_item_total_discount(self):
        from utils.orders.order import OrderItemUtils  # isort: skip

        return OrderItemUtils.calculate_item_total_discount(self)

    @property
    def calculate_total_amount(self):
        from utils.orders.order import OrderItemUtils  # isort: skip

        return OrderItemUtils.calculate_total_amount(self)

    @property
    def get_image(self):
        from utils.orders.order import OrderItemUtils  # isort: skip

        return OrderItemUtils.get_image(self)

    @property
    def catalog_name(self):
        from utils.orders.order import OrderItemUtils  # isort: skip

        return OrderItemUtils.catalog_name(self)

    def save(self, *args, **kwargs):

        self.sub_total = self.calculate_sub_total
        self.total_amount = self.calculate_total_amount
        self.image = self.get_image
        super().save(*args, **kwargs)
        self.order.save(
            update_fields=[
                "total_amount",
                "total_items",
                "sub_total_amount",
                "total_discount",
            ]
        )

    class Meta:
        unique_together = ["order", "object_id", "content_type"]
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.quantity} × {self.content_object} in Order {self.order.id}"


# for the case of a model that is global (e.g DeliveryMethod, PaymentMethod), they don't need a user attribute, unlike a model whose object will be peculiar to each user (e.g Order, Address)


# total = order.orderitems.aggregate(total=Sum(ExpressionWrapper(F('quantity') * F('unit_price') - F('discount_amount'),output_field=DecimalField())))['total']
# print("Calculated total:", total)
# print("Stored total:", order.total_amount)
