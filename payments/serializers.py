from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from core.choices import (
    DeliveryStatus,
    PaymentMethodChoice,
    RefundMethodChoice,
    ReturnStatus,
)
from order.models import OrderItem
from payments.models import Payment, PaymentMethod, ReturnRequest
from payments.tasks import process_paystack_return


class PaymentMethodSerializer(serializers.ModelSerializer):
    display_code = serializers.CharField(source="get_code_display", read_only=True)

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
            "code",
            "display_code",
            "description",
            "status",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%a %d, %b")
    processed_at = serializers.DateTimeField(format="%a %d, %b.", read_only=True)
    paid_at = serializers.DateTimeField(format="%a %d, %b", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "payment_method_code",
            "amount",
            "currency",
            "status",
            "failure_reason",
            "reference",
            "created_at",
            "processed_at",
            "paid_at",
        )


class InitiatePaymentSerializer(serializers.Serializer):
    method_code = serializers.ChoiceField(choices=PaymentMethodChoice.choices)


class InitiatePaymentResponseSerializer(serializers.Serializer):
    authorization_url = serializers.URLField(required=False)
    reference = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    order_id = serializers.CharField(required=False)


class PaymentCallbackSerializer(serializers.Serializer):
    reference = serializers.CharField(
        required=True, error_messages={"required": "Payment reference is required."}
    )


class ReturnRequestCreateSerializer(serializers.ModelSerializer):
    order_number = serializers.UUIDField(source="order.order_number", read_only=True)
    order_item_id = serializers.UUIDField(
        required=False, allow_null=True, write_only=True
    )
    requested_date = serializers.DateTimeField(
        source="created_at", format="%a %d, %b", read_only=True
    )

    def validate(self, data):

        order = self.context.get("order")
        order_item_id = data.get("order_item_id")
        order_item = order.items.filter(id=order_item_id).first()

        if order.delivery_status != DeliveryStatus.DELIVERED:
            raise serializers.ValidationError(
                {"message": "You can only request return for delivered orders"}
            )

        if order.delivered_at:
            deadline = order.delivered_at + timedelta(days=7)
            if timezone.now() > deadline:
                raise serializers.ValidationError(
                    {
                        "message": "The 7-day return policy window for this order has expired."
                    }
                )

        if not order_item_id and order.return_requests.exists():
            raise serializers.ValidationError(
                {
                    "message": "A return request has already been made for this order or one of its items."
                }
            )

        if (
            order.return_requests.filter(order_item__isnull=True)
            and order.return_requests.exists()
        ):
            raise serializers.ValidationError(
                {
                    "message": "A return request has been made for this order already or an item in this order"
                }
            )

        if order_item_id:
            if not order_item:
                raise serializers.ValidationError(
                    {"message": "This item does not belong to the specified order."}
                )

            if order.return_requests.filter(order_item=order_item).exists():
                raise serializers.ValidationError(
                    {
                        "message": "A return request has already been submitted for this item."
                    }
                )

        data["order_item_obj"] = order_item
        return data

    def create(self, validated_data):

        request = self.context.get("request")
        user = request.user
        order = self.context.get("order")

        order_item_object = validated_data.pop("order_item_obj", None)

        return_amount = (
            order_item_object.total_amount if order_item_object else order.total_amount
        )

        return_request = ReturnRequest.objects.create(
            reason=validated_data.get("reason"),
            user=user,
            order=order,
            order_item=order_item_object,
            evidence_image=validated_data.get("evidence_image"),
            return_amount=return_amount,
            refund_method=order.payment_method_name,
        )

        return return_request

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "order_item_id",
            "order_number",
            "return_number",
            "reason",
            "evidence_image",
            "status",
            "return_amount",
            "requested_date",
        )
        read_only_fields = (
            "id",
            "return_number",
            "status",
            "requested_date",
            "return_amount",
        )


class OrderItemRefundSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        catalog_item = OrderItemSerializerUtils.get_catalog_item(self, obj)

        if not catalog_item:
            return None

        name = catalog_item.name
        return name

    class Meta:
        model = OrderItem
        fields = ("id", "image", "name")


class OrderItemDetailsRefundSerializer(serializers.ModelSerializer):
    item_details_url = serializers.SerializerMethodField()
    model_name = serializers.CharField(source="content_type.model")

    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        catalog_item = OrderItemSerializerUtils.get_catalog_item(self, obj)

        if not catalog_item:
            return None

        name = catalog_item.name
        return name

    def get_item_details_url(self, obj):
        from utils.orders.order import OrderItemSerializerUtils  # isort: skip

        return OrderItemSerializerUtils.get_item_details_url(self, obj)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "image",
            "name",
            "model_name",
            "quantity",
            "total_amount",
            "item_details_url",
        )


class ReturnRequestSingleItemSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    order_item = OrderItemRefundSerializer()
    details_url = serializers.SerializerMethodField()
    update_url = serializers.SerializerMethodField()
    tracking_url = serializers.SerializerMethodField()
    requested_date = serializers.DateTimeField(source="created_at", format="%a %d, %b")
    processed_date = serializers.DateTimeField(
        source="processed_at", format="%a %d, %b.", read_only=True
    )

    def get_details_url(self, obj):
        request = self.context.get("request")
        return_number = obj.return_number
        url = reverse(
            "return_request_details",
            kwargs={"return_number": return_number},
            request=request,
        )
        return url

    def get_update_url(self, obj):
        request = self.context.get("request")
        return_id = obj.id
        user = request.user
        if user.is_staff:
            return reverse(
                "return_manage_admin", kwargs={"return_id": return_id}, request=request
            )
        return reverse(
            "return_manage_customer", kwargs={"return_id": return_id}, request=request
        )

    def get_tracking_url(self, obj):
        request = self.context.get("request")
        return_number = obj.return_number
        tracking_id = obj.return_tracking_id
        url = reverse(
            "return_tracking",
            kwargs={"tracking_id": tracking_id, "return_number": return_number},
            request=request,
        )
        return url

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "return_number",
            "order_number",
            "details_url",
            "update_url",
            "tracking_url",
            "order_item",
            "reason",
            "status",
            "return_amount",
            "requested_date",
            "processed_date",
        )
        read_only_fields = fields

    # def get_order_item_name(self, obj):
    #     if obj.order_item and hasattr(obj.order_item, "content_object"):
    #         return str(obj.order_item.content_object)
    #     return "Full Order Return"


class ReturnRequestFullOrderSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    orderitems = OrderItemRefundSerializer(
        required=False, source="order.items", many=True
    )
    details_url = serializers.SerializerMethodField()
    update_url = serializers.SerializerMethodField()
    tracking_url = serializers.SerializerMethodField()
    requested_date = serializers.DateTimeField(source="created_at", format="%a %d, %b")
    processed_date = serializers.DateTimeField(
        source="processed_at", format="%a %d, %b.", read_only=True
    )

    def get_details_url(self, obj):
        request = self.context.get("request")
        return_number = obj.return_number
        url = reverse(
            "return_request_details",
            kwargs={"return_number": return_number},
            request=request,
        )
        return url

    def get_update_url(self, obj):
        request = self.context.get("request")
        return_id = obj.id
        user = request.user
        if user.is_staff:
            return reverse(
                "return_manage_admin", kwargs={"return_id": return_id}, request=request
            )
        return reverse(
            "return_manage_customer", kwargs={"return_id": return_id}, request=request
        )

    def get_tracking_url(self, obj):

        request = self.context.get("request")
        return_number = obj.return_number
        tracking_id = obj.return_tracking_id

        if not tracking_id:
            return None

        url = reverse(
            "return_tracking",
            kwargs={"tracking_id": tracking_id, "return_number": return_number},
            request=request,
        )
        return url

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "return_number",
            "order_number",
            "details_url",
            "update_url",
            "tracking_url",
            "orderitems",
            "reason",
            "status",
            "return_amount",
            "requested_date",
            "processed_date",
        )
        read_only_fields = fields


class ReturnRequestListSerializer(serializers.Serializer):
    single_item_return_request = ReturnRequestSingleItemSerializer(
        many=True, required=False, read_only=True
    )
    full_order_return_request = ReturnRequestFullOrderSerializer(
        many=True, required=False, read_only=True
    )

    # class Meta:
    #     model = ReturnRequest
    #     fields = (
    #         "single_item_return_request ",
    #         "full_order_return_request",
    #     )

    #     read_only_fields = fields


class ReturnRequestDetailSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    order_item = serializers.SerializerMethodField()
    requested_date = serializers.DateTimeField(source="created_at", format="%a %d, %b")
    approved_date = serializers.DateTimeField(
        source="approved_at", format="%a %d, %b.", read_only=True
    )
    processed_date = serializers.DateTimeField(
        source="processed_at", format="%a %d, %b.", read_only=True
    )

    def get_order_item(self, obj):

        items = (
            [obj.order_item] if obj.order_item is not None else obj.order.items.all()
        )
        serialized_items = OrderItemDetailsRefundSerializer(
            items, context=self.context, many=True
        ).data
        return serialized_items

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "return_number",
            "order_number",
            "user_email",
            "order_item",
            "reason",
            "evidence_image",
            "refund_receipt_image",
            "status",
            "refund_method",
            "return_tracking_id",
            "return_amount",
            "admin_notes",
            "rejection_reason",
            "requested_date",
            "approved_date",
            "processed_date",
        )
        read_only_fields = fields

    # def get_order_item_name(self, obj):
    #     if obj.order_item and hasattr(obj.order_item, "content_object"):
    #         return str(obj.order_item.content_object)
    #     return "Full Order Return"


class ReturnRequestCustomerManageSerializer(serializers.ModelSerializer):
    update_url = serializers.SerializerMethodField()
    id = serializers.IntegerField(read_only=True)

    def validate(self, data):

        if self.instance and self.instance.status != ReturnStatus.PENDING:
            raise serializers.ValidationError(
                {
                    "message": "You can only update your return request while it is pending review."
                }
            )
        return data

    def get_update_url(self, obj):
        request = self.context.get("request")
        return_id = obj.id
        user = request.user
        if user.is_staff:
            return reverse(
                "return_manage_admin", kwargs={"return_id": return_id}, request=request
            )
        return reverse(
            "return_manage_customer", kwargs={"return_id": return_id}, request=request
        )

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "evidence_image",
            "reason",
            "update_url",
        )


class ReturnRequestAdminManageSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source="order.order_number", read_only=True)
    requested_date = serializers.DateTimeField(
        source="created_at", read_only=True, format="%a %d, %b"
    )
    processed_date = serializers.DateTimeField(
        source="processed_at", read_only=True, format="%a %d, %b"
    )

    action = serializers.ChoiceField(
        choices=ReturnStatus.choices, required=False, write_only=True
    )
    admin_notes = serializers.CharField(required=False)
    rejection_reason = serializers.CharField(required=False)
    update_url = serializers.SerializerMethodField()

    def validate(self, data):

        action = data.get("action")
        rejection_reason = (
            data.get("rejection_reason") if data.get("rejection_reason") else None
        )

        if action in [
            ReturnStatus.APPROVED,
            ReturnStatus.UNDER_REVIEW,
            ReturnStatus.REJECTED,
        ]:
            if self.instance.status == action:
                raise serializers.ValidationError(
                    {
                        "message": "This action has been carried out already consider another action"
                    }
                )

        if action in [ReturnStatus.COMPLETED, ReturnStatus.PROCESSING]:
            raise serializers.ValidationError(
                {
                    "message": "You can no longer perform any action on this return request as the request is being processed or completed"
                }
            )

        if self.instance and self.instance.status == ReturnStatus.APPROVED:
            if action in [ReturnStatus.UNDER_REVIEW, ReturnStatus.REJECTED]:
                raise serializers.ValidationError(
                    {"message": "You cannot reject or review a request after approval"}
                )

        if self.instance.status != ReturnStatus.UNDER_REVIEW:
            if action in [ReturnStatus.APPROVED, ReturnStatus.REJECTED]:
                raise serializers.ValidationError(
                    {
                        "message": "Request has to be under review first before APPROVAL OR REJECTION"
                    }
                )

        return data

    def get_update_url(self, obj):
        request = self.context.get("request")
        return_id = obj.id
        user = request.user
        if user.is_staff:
            return reverse(
                "return_manage_admin", kwargs={"return_id": return_id}, request=request
            )
        return reverse(
            "return_manage_customer", kwargs={"return_id": return_id}, request=request
        )

    def update(self, instance, validated_data):

        action = validated_data.get("action")
        admin_notes = validated_data.get("admin_notes")
        rejection_reason = validated_data.get("rejection_reason")

        # user = request.user # note that user here is admin bekos it's admin that will update the request model, the customer will just be the one to create it.

        if action in [
            ReturnStatus.APPROVED,
            ReturnStatus.UNDER_REVIEW,
            ReturnStatus.COMPLETED,
        ]:
            instance.status = action
            instance.admin_notes = admin_notes if admin_notes else None

        elif action == ReturnStatus.REJECTED:
            instance.status = action
            instance.admin_notes = admin_notes
            instance.rejection_reason = rejection_reason

        instance.save()

        if action == ReturnStatus.APPROVED:
            if (
                instance.refund_method == RefundMethodChoice.PAYSTACK
                or instance.order.payment_method_name == PaymentMethodChoice.PAYSTACK
            ):
                process_paystack_return.delay(
                    return_id=instance.id, user_id=instance.user.id
                )

        return instance

    class Meta:
        model = ReturnRequest
        fields = (
            "order_number",
            "return_number",
            "reason",
            "status",
            "requested_date",
            "processed_date",
            "admin_notes",
            "return_amount",
            "refund_receipt_image",
            "action",
            "rejection_reason",
            "update_url",
        )

        read_only_fields = (
            "order_number",
            "return_number",
            "reason",
            "status",
            "requested_date",
            "processed_date",
            "return_amount",
            "update_url",
        )


class ReturnRequestTrackingSerializer(serializers.ModelSerializer):
    timeline = serializers.SerializerMethodField()

    def get_timeline(self, obj):
        from utils.payments.payment import TrackingReturnRequestSerializerUtils  # isort: skip

        return TrackingReturnRequestSerializerUtils.get_timeline(obj)

    class Meta:
        model = ReturnRequest
        fields = (
            "id",
            "return_number",
            "return_tracking_id",
            "status",
            "timeline",
        )
