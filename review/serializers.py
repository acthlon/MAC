from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from materials.models import Materials
from order.models import OrderItem
from products.models import Products
from review.models import Reviews


class ItemReviewSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(read_only=True)
    rating_display = serializers.CharField(source="get_rating_display", read_only=True)
    date_created = serializers.DateTimeField(
        source="created_at", read_only=True, format="%B %d %Y"
    )
    date_updated = serializers.DateTimeField(
        source="updated_at", read_only=True, format="%B %d %Y"
    )
    profile_image = serializers.ImageField(source="user.profile_image")

    def get_username(self, obj):

        username = obj.user.username if obj.user and obj.user.username else "Anonymous"

        first_two_letters = obj.user.username[:2]
        last_two_letters = obj.user.username[-2:]
        combined = f"{first_two_letters}***{last_two_letters}"
        return combined

    class Meta:
        model = Reviews
        fields = (
            "id",
            "username",
            "profile_image",
            "comment",
            "purchase_verified",
            "rating",
            "rating_display",
            "date_updated",
            "date_created",
        )
        read_only_fields = ("purchase_verified",)


class ReviewListSerializer(ItemReviewSerializer):
    class Meta(ItemReviewSerializer.Meta):
        model = Reviews
        fields = ItemReviewSerializer.Meta.fields


class ReviewWriteSerializer(serializers.ModelSerializer):
    def validate(self, data):
        request = self.context.get("request")
        user = request.user
        item_id = self.context.get("item_id")
        model_name = self.context.get("model_name")

        model_class = Materials if model_name == "materials" else Products
        content_type = ContentType.objects.get_for_model(model_class)

        already_reviewed = Reviews.objects.filter(
            user=request.user, object_id=item_id, content_type=content_type
        ).exists()

        if already_reviewed:
            raise serializers.ValidationError(
                "You have already created a review for this item."
            )

        has_permission = OrderItem.objects.filter(
            order__user=user,
            object_id=item_id,
            content_type=content_type,
            order__status="COMPLETED",
            order__is_active=False,
        ).exists()  # NOTE: use choices insgtead of hardcoding COMPLETED here.

        if not has_permission:
            raise serializers.ValidationError(
                "You can only make review for an item you have purchased and received"
            )

        data["purchase_verified"] = True

        self.context["content_type"] = content_type
        return data

    def create(self, validated_data):

        user = self.context.get("request").user
        item_id = self.context.get("item_id")
        content_type = self.context.get("content_type")

        review = Reviews.objects.create(
            **validated_data, content_type=content_type, object_id=item_id, user=user
        )

        return review

    class Meta:
        model = Reviews
        fields = ("comment", "rating", "purchase_verified")
        read_only_fields = ("purchase_verified",)
