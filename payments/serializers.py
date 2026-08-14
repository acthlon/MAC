from rest_framework import serializers

from core.choices import ActionStatus
from payments.models import Payment, RefundRequest


class PaymentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "payment_method",
            "amount",
            "currency",
            "status",
            "reference",
            "created_at",
            "updated_at",
        )


class InitiatePaymentSerializer(serializers.Serializer):
    method_code = serializers.CharField()


class RefundRequestSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="order", read_only=True)

    def create(self, validated_data):

        request = self.context.get("request")
        user = request.user
        order = self.context.get("order")

        refund_request = RefundRequest.objects.create(
            reason=validated_data["reason"], user=user, order=order, status="pending"
        )

        refund_request.save()
        return refund_request

    class Meta:
        model = RefundRequest
        fields = (
            "order_id",
            "reason",
            "status",
            "requested_at",
            "admin_notes",
            "refund_amount",
        )
        read_only_fields = ("status", "requested_at", "refund_amount")


class RefundRequestUpdateSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(
        choices=ActionStatus.choices, required=True, write_only=True
    )

    def update(self, instance, validated_data):

        action = validated_data.get("action")
        admin_notes = validated_data.get("admin_note")

        # user = request.user # note that user here is admin bekos it's admin that will update the request model, the customer will just be the one to create it.

        if action == "APPROVED":
            instance.status = action
            instance.refund_amount = instance.order.total_amount
            instance.admin_notes = admin_notes

        elif action == "REJECTED":
            instance.status = action
            instance.admin_notes = admin_notes
            instance.refund_amount = None

        instance.save()
        return instance

    class Meta:
        model = RefundRequest
        fields = (
            "order_id",
            "reason",
            "status",
            "requested_at",
            "admin_notes",
            "refund_amount",
            "processed_at",
            "action",
        )
        read_only_fields = ("processed_at",)
