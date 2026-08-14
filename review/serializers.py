from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from materials.models import Materials
from order.models import OrderItem
from products.models import Products
from review.models import Reviews


class ReviewListSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%B %d, %Y")
    updated_at = serializers.DateTimeField(format="%B %d, %Y")
    item_average_rating = serializers.SerializerMethodField(
        read_only=True, required=False
    )

    def get_item_average_rating(self, obj):
        return obj.item_average_rating

    def get_first_name(self, obj):
        return obj.user.first_name.capitalize() if obj.user.first_name else None

    def get_last_name(self, obj):
        return obj.user.last_name[0].upper() if obj.user.last_name else None

    def get_profile_image(self, obj):
        request = self.context.get("request")
        if obj.user.profile_image:
            image = obj.user.profile_image
            image_url = request.build_absolute_uri(image.url)
            return image_url if image else None

    class Meta:
        model = Reviews
        fields = [
            "first_name",
            "last_name",
            "profile_image",
            "comment",
            "rating",
            "created_at",
            "updated_at",
            "item_average_rating",
        ]
        read_only_fields = ["verified_purchase"]


class ReviewCreateSerializer(serializers.ModelSerializer):
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

        data["verified_purchase"] = True

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
        fields = ("comment", "rating", "verified_purchase")


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reviews
        fields = ("comment", "rating", "verified_purchase")
        read_only_fields = ["verified_purchase"]


class ProductDetailReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    rating_display = serializers.CharField(source="get_rating_display", read_only=True)
    date = serializers.SerializerMethodField(read_only=True)

    def get_date(self, obj):
        return obj.created_at.strftime("%B %d, %Y")

    class Meta:
        model = Reviews
        fields = (
            "id",
            "username",
            "comment",
            "verified_purchase",
            "rating",
            "rating_display",
            "date",
        )


class MaterialDetailReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    rating_display = serializers.CharField(source="get_rating_display", read_only=True)
    date = serializers.SerializerMethodField(read_only=True)

    def get_date(self, obj):
        return obj.created_at.strftime("%B %d, %Y")

    class Meta:
        model = Reviews
        fields = (
            "id",
            "username",
            "comment",
            "verified_purchase",
            "rating",
            "rating_display",
            "date",
        )
