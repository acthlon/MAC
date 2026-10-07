from decimal import Decimal

from django.conf import settings
from django.db import transaction
from paystackapi.transaction import Transaction
from rest_framework import serializers
from rest_framework.reverse import reverse

from cart.models import Cart
from cart.serializers import CartItemSerializer, CartSummarySerializer
from core.choices import OrderStatus, PaymentMethodChoice, PaymentStatus, Status
from order.models import (
    Address,
    DeliveryMethod,
    Order,
    OrderItem,
)
from payments.models import Payment, PaymentMethod
from payments.serializers import PaymentMethodSerializer


class AddressSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    create_address_url = serializers.SerializerMethodField(read_only=True)
    update_address_url = serializers.SerializerMethodField(read_only=True)
    delete_address_url = serializers.SerializerMethodField(read_only=True)

    def get_create_address_url(self, obj):
        request = self.context.get("request")
        url = reverse("address_create", request=request)
        return url

    def get_update_address_url(self, obj):
        request = self.context.get("request")
        url = (
            reverse("address_update_delete", kwargs={"pk": obj.id}, request=request)
            if obj
            else None
        )
        return url

    def get_delete_address_url(self, obj):
        return self.get_update_address_url(obj)

    class Meta:
        model = Address
        fields = [
            "id",
            "user",
            "first_name",
            "last_name",
            "phone_number",
            "alternative_phone_number",
            "delivery_address",
            "email",
            "city",
            "state",
            "country",
            "address_type",
            "is_default",
            "additional_info",
            "create_address_url",
            "delete_address_url",
            "update_address_url",
        ]
        read_only_fields = ["id"]


class DeliveryMethodSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source="get_name_display", read_only=True)

    class Meta:
        model = DeliveryMethod
        fields = [
            "id",
            "name",
            "name_display",
            "description",
            "cost",
            "estimated_date",
            "status",
            "is_selected",
        ]
        read_only_fields = ("id", "name_display", "estimated_date")


class OrderSummarySerializer(CartSummarySerializer):
    shipping_fee = serializers.SerializerMethodField()

    def get_shipping_fee(self, obj):
        request = self.context.get("request")
        user = request.user
        delivery_method_id = request.query_params.get("delivery_method_id")

        delivery_method_object = (
            DeliveryMethod.objects.get(id=delivery_method_id)
            if delivery_method_id
            else None
        )
        cost = (
            delivery_method_object.cost if delivery_method_object else Decimal("0.00")
        )

        return cost


class CheckoutPreviewSerializer(serializers.ModelSerializer):
    delivery_address = serializers.SerializerMethodField()
    delivery_methods = serializers.SerializerMethodField()
    items = CartItemSerializer(many=True)
    payment_methods = serializers.SerializerMethodField()

    order_summary = OrderSummarySerializer(source="*")
    place_order_url = serializers.SerializerMethodField()

    def get_delivery_address(
        self, obj
    ):  # NOTE: The obj here is the object passed to the particular serializer class from the views we are under and if no object is passed to it from the views, then the obj=None
        request = self.context.get("request")
        user = request.user

        if request and request.user.is_authenticated:
            queryset = Address.objects.filter(user=user)
            queryset_serialized = AddressSerializer(
                queryset, many=True, context=self.context
            ).data
            return queryset_serialized
        return []

    def get_delivery_methods(self, obj):
        queryset = DeliveryMethod.objects.filter(status=Status.ACTIVE)
        serialized_queryset = DeliveryMethodSerializer(
            queryset, many=True, context=self.context
        ).data
        return serialized_queryset

    def get_payment_methods(self, obj):
        queryset = PaymentMethod.objects.filter(status=Status.ACTIVE)
        serialized_queryset = PaymentMethodSerializer(
            queryset, many=True, context=self.context
        ).data
        return serialized_queryset

    def get_place_order_url(self, obj):
        request = self.context.get("request")
        url = reverse("place_order", request=request)
        return url

    class Meta:
        model = Cart
        fields = [
            "place_order_url",
            "delivery_address",
            "delivery_methods",
            "items",
            "payment_methods",
            "order_summary",
        ]


class CreateOrderFromCartSerializer(serializers.ModelSerializer):
    delivery_address_id = serializers.UUIDField(required=True, write_only=True)
    delivery_method_id = serializers.IntegerField(required=True, write_only=True)
    payment_method_id = serializers.UUIDField(required=True, write_only=True)

    authorization_url = serializers.CharField(read_only=True)
    payment_reference = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True)
    date_created = serializers.DateTimeField(
        source="created_at", format="%a %d, %b.", read_only=True
    )

    def validate_delivery_method_id(self, value):
        try:
            return DeliveryMethod.objects.get(id=value)
        except DeliveryMethod.DoesNotExist:
            raise serializers.ValidationError("Delivery method not found.")

    def validate_delivery_address_id(self, value):
        user = self.context.get("request").user
        try:
            return Address.objects.get(id=value, user=user)
        except Address.DoesNotExist:
            raise serializers.ValidationError(
                "Delivery address not found for the current user."
            )

    def validate_payment_method_id(self, value):
        try:
            return PaymentMethod.objects.get(id=value)
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Payment method not found.")

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user

        delivery_address_obj = validated_data.pop("delivery_address_id")
        payment_method_obj = validated_data.pop("payment_method_id")
        delivery_method_obj = validated_data.pop("delivery_method_id")

        shipping_address = AddressSerializer(delivery_address_obj).data
        shipping_address.pop("create_address_url", None)
        shipping_address.pop("update_address_url", None)
        shipping_address.pop("delete_address_url", None)
        shipping_address.pop("id", None)
        shipping_address.pop("is_default", None)

        with transaction.atomic():
            cart = Cart.objects.filter(user=user).select_for_update().first()

            last_order = Order.objects.filter(user=user).order_by("-created_at").first()

            # CRITICAL FIX: Only run these errors IF the cart is actually empty!
            if not cart or not cart.items.exists():
                last_order = (
                    Order.objects.filter(user=user).order_by("-created_at").first()
                )
                if last_order:
                    if (
                        last_order.status == OrderStatus.CONFIRMED
                        and last_order.payment_status == PaymentStatus.PENDING
                    ):
                        raise serializers.ValidationError(
                            {"message": "Your order has been placed successfully."}
                        )
                    elif (
                        last_order.status == OrderStatus.CREATED
                        and last_order.payment_status == PaymentStatus.PENDING
                    ):
                        raise serializers.ValidationError(
                            {
                                "message": f"You have a pending payment for order {last_order.order_number}."
                            }
                        )

                raise serializers.ValidationError({"message": "Your cart is empty."})

            order = Order.objects.create(
                user=user,
                shipping_address_snapshot=shipping_address,
                delivery_method_name=delivery_method_obj.name,
                payment_method_name=payment_method_obj.code,
                shipping_fee=delivery_method_obj.cost,
            )

            cart_items = cart.items.select_related("content_type").all()
            for cart_item in cart_items:
                item = cart_item.content_object
                image_url = getattr(item, "get_variant_pry_image", None) or getattr(
                    getattr(item, "variant", None), "get_variant_pry_image", None
                )

                orderitems = OrderItem.objects.create(
                    order=order,
                    content_type=cart_item.content_type,
                    object_id=cart_item.object_id,
                    quantity=cart_item.quantity,
                    image=image_url,
                    unit_price=item.calculate_variant_actual_unit_price,
                    discount=item.calculate_variant_discount,
                )

            order.save()

            payment = Payment.objects.create(
                user=user,
                order=order,
                payment_method_code=payment_method_obj.code,
                amount=order.total_amount,
                currency="NGN",
            )

            cart.items.all().delete()

        # Intializing Payment
        if payment.payment_method_code == PaymentMethodChoice.PAYSTACK:
            amount_in_kobo = int(order.total_amount * 100)
            paystack_tx = Transaction(secret_key=settings.PAYSTACK_SECRET_KEY)

            callback_url = reverse("payment_callback", request=request)
            customer_email = (order.shipping_address_snapshot or {}).get(
                "email"
            ) or user.email

            paystack_response = paystack_tx.initialize(
                email=customer_email,
                amount=amount_in_kobo,
                reference=str(payment.id),
                currency="NGN",
                callback_url=callback_url,
                metadata={"order_id": str(order.id), "payment_id": str(payment.id)},
                label=f"Checkout_{order.id}",
            )

            if paystack_response.get("status"):
                reference = paystack_response.get("data", {}).get("reference")
                auth_url = paystack_response.get("data", {}).get("authorization_url")

                with transaction.atomic():
                    order.payment_reference = reference
                    payment.reference = reference
                    payment.status = PaymentStatus.INITIALIZED

                    order.save(update_fields=["payment_reference"])
                    payment.save(update_fields=["reference", "status"])

                    order.authorization_url = auth_url
                    order.payment_reference = reference

            else:
                payment.status = PaymentStatus.FAILED
                payment.save()
                raise serializers.ValidationError(
                    {"detail": "Payment initialization failed"}
                )

        elif payment.payment_method_code == PaymentMethodChoice.CASH_ON_DELIVERY:
            with transaction.atomic():
                # Deduct stock from products using row locking
                for order_item in order.items.select_related("content_type").all():
                    ModelClass = order_item.content_type.model_class()

                    # 1. Fetch and lock the specific variant/item row
                    locked_item = ModelClass.objects.select_for_update().get(
                        pk=order_item.object_id
                    )

                    if hasattr(locked_item, "stock"):
                        if locked_item.stock >= order_item.quantity:
                            locked_item.stock -= order_item.quantity
                            locked_item.save(update_fields=["stock"])
                        else:
                            raise serializers.ValidationError(
                                {
                                    "message": f"Sorry, this item is out of stock. Only {locked_item.stock} is available."
                                }
                            )

                order.status = OrderStatus.CONFIRMED
                order.save()
                order.message = "Order placed successfully with Cash on Delivery"

        else:
            raise serializers.ValidationError({"message": "Unsupported payment method"})

        return order

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "delivery_address_id",
            "payment_method_id",
            "delivery_method_id",
            "status",
            "payment_status",
            "authorization_url",
            "payment_reference",
            "message",
            "date_created",
        ]

        read_only_fields = [
            "id",
            "order_number",
            "status",
            "payment_status",
            "authorization_url",
            "payment_reference",
            "date_created",
        ]


class OrderItemListSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source="content_type.model")
    name = serializers.SerializerMethodField()
    item_create_review_url = serializers.SerializerMethodField()
    refund_request_url = serializers.SerializerMethodField()
    tracking_order_url = serializers.SerializerMethodField()
    item_details_url = serializers.SerializerMethodField()

    def get_name(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        catalog_item = OrderItemSerializerUtils.get_catalog_item(obj)

        if not catalog_item:
            return None

        name = catalog_item.name
        return name

    def get_item_create_review_url(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        return OrderItemSerializerUtils.get_item_create_review_url(self, obj)

    def get_refund_request_url(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        return OrderItemSerializerUtils.get_refund_request_url(self, obj)

    def get_tracking_order_url(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        return OrderItemSerializerUtils.get_tracking_order_url(self, obj)

    def get_item_details_url(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        return OrderItemSerializerUtils.get_item_details_url(self, obj)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "item_create_review_url",
            "refund_request_url",
            "tracking_order_url",
            "item_details_url",
            "image",
            "name",
            "model_name",
            "quantity",
            "unit_price",
            "total_amount",
        ]
        read_only_fields = ["id"]


class OrderItemSerializer(OrderItemListSerializer):
    class Meta(OrderItemListSerializer.Meta):
        model = OrderItem
        fields = OrderItemListSerializer.Meta.fields + [
            "sub_total",
            "discount",
        ]
        read_only_fields = ["id"]


class OrderListSerializer(serializers.ModelSerializer):
    orderitems = OrderItemListSerializer(many=True, source="items")
    ordered_day = serializers.ReadOnlyField(source="get_ordered_day")
    delivered_day = serializers.ReadOnlyField(source="get_delivered_day")
    order_details_url = serializers.SerializerMethodField()

    def get_order_details_url(self, obj):
        request = self.context.get("request")
        order_number = obj.order_number if obj else None

        url = reverse(
            "order_details", kwargs={"order_number": order_number}, request=request
        )

        return url

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "ordered_day",
            "delivered_day",
            "order_details_url",
            "orderitems",
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    orderitems = OrderItemSerializer(source="items", many=True)
    ordered_day = serializers.ReadOnlyField(source="get_ordered_day")
    delivered_day = serializers.ReadOnlyField(source="get_delivered_day")
    order_lists_url = serializers.SerializerMethodField()
    initialize_payment_url = serializers.SerializerMethodField()

    def get_order_lists_url(self, obj):

        request = self.context.get("request")
        url = reverse("order_list", request=request)
        return url

    def get_initialize_payment_url(self, obj):
        request = self.context.get("request")

        url = (
            reverse("initialize_payment", kwargs={"pk": obj.id}, request=request)
            if obj.status in [OrderStatus.CREATED, OrderStatus.FAILED]
            and obj.payments.first().status == PaymentStatus.FAILED
            else None
        )

        return url

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "ordered_day",
            "delivered_day",
            "order_lists_url",
            "payment_status",
            "payment_reference",
            "initialize_payment_url",
            "delivery_method_name",
            "payment_method_name",
            "tracking_id",
            "total_items",
            "sub_total_amount",
            "shipping_fee",
            "total_discount",
            "total_amount",
            "customer_note",
            "shipping_address_snapshot",
            "orderitems",
        ]


class TrackingOrderSerializer(serializers.ModelSerializer):
    timeline = serializers.SerializerMethodField()

    def get_timeline(self, obj):

        from utils.orders.order import TrackingOrderSerializerUtils  # isort: skip

        return TrackingOrderSerializerUtils.get_timeline(obj)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "tracking_id",
            "status",
            "delivery_status",
            "timeline",
        ]
