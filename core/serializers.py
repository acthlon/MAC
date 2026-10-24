import datetime

from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from core.models import Banner, Category
from review.serializers import ItemReviewSerializer
from utils.reviews.review import ReviewAnalyticsUtils


class CatalogItemCategoriesReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "status")


class BaseCatalogCardSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    model_type = serializers.CharField(source="_meta.model_name")
    category = serializers.CharField(source="categories")
    quality_category = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    pry_image = serializers.ImageField(source="get_pry_image", read_only=True)
    avg_rating = serializers.ReadOnlyField(
        source="calculate_average_rating", required=False
    )
    review_count = serializers.IntegerField(
        source="calculate_review_count", read_only=True, required=False
    )
    discounted_price = serializers.DecimalField(
        source="calculate_discounted_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    is_new_arrival = serializers.SerializerMethodField()

    percent_discount = serializers.ReadOnlyField(
        source="calculate_percent_discount", required=False
    )

    item_detail_url = serializers.SerializerMethodField(read_only=True, required=False)
    add_to_cart_url = serializers.SerializerMethodField(read_only=True)

    def get_add_to_cart_url(self, obj):
        request = self.context.get("request")
        url = reverse("add_to_cart", request=request)
        return url

    def get_item_detail_url(self, obj):
        request = self.context.get("request")
        reverse_name = (
            "material_details"
            if obj._meta.model_name == "materials"
            else "product_details"
        )
        url = reverse(
            reverse_name, kwargs={"slug": obj.slug, "pk": obj.id}, request=request
        )
        return url

    def get_is_new_arrival(self, obj):
        # 1. Figure out what the date was exactly 7 days ago
        seven_days_ago = timezone.now() - datetime.timedelta(days=7)
        is_new = obj.created_at >= seven_days_ago
        return is_new


class CategorySerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField(read_only=True)
    name_display = serializers.CharField(source="get_name_display", read_only=True)
    type_label = serializers.SerializerMethodField()

    def get_type_label(self, obj):

        type_label = "Ready-Made" if obj.target_model.model == "products" else "Fabrics"

        return type_label if obj.target_model else None

    def get_link(self, obj):
        request = self.context.get("request")
        item_list_url = (
            reverse("product_list", request=request)
            if obj.target_model and obj.target_model.model == "products"
            else reverse("material_list", request=request)
        )
        return f"{item_list_url}?categories={obj.name}" if obj.name else "#"

    class Meta:
        model = Category
        fields = (
            "id",
            "target_model",
            "name",
            "name_display",
            "type_label",
            "image",
            "description",
            "link",
        )

        extra_kwargs = {
            "target_model": {"write_only": True},
            "image": {"write_only": True},
            "status": {"write_only": True},
            "description": {"write_only": True},
        }


class BannerSeralizer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = (
            "id",
            "tag",
            "titlePrefix",
            "titleHighlight",
            "subtitle",
            "description",
            "primaryCta",
            "primaryPath",
            "secondaryCta",
            "secondaryPath",
            "image",
            "status",
        )


class HomePageSerializer(serializers.Serializer):
    average_rating = serializers.SerializerMethodField(read_only=True)
    total_customers = serializers.SerializerMethodField(read_only=True)
    satisfaction_rate = serializers.SerializerMethodField(read_only=True)
    hero_actions = serializers.SerializerMethodField(read_only=True)

    banners = BannerSeralizer(read_only=True, many=True)
    product_categories = CategorySerializer(read_only=True, many=True)
    material_categories = CategorySerializer(read_only=True, many=True)

    featured_products = BaseCatalogCardSerializer(read_only=True, many=True)
    new_arrivals = BaseCatalogCardSerializer(read_only=True, many=True)
    reviews = ItemReviewSerializer(read_only=True, many=True)

    def get_average_rating(self, obj):
        return ReviewAnalyticsUtils.calculate_total_average_rating()

    def get_total_customers(self, obj):
        return ReviewAnalyticsUtils.calculate_total_customers()

    def get_satisfaction_rate(self, obj):
        return ReviewAnalyticsUtils.calculate_satisfacton_rate()

    def get_hero_actions(self, obj):
        request = self.context.get("request")
        product_list_url = reverse("product_list", request=request)
        material_list_url = reverse("material_list", request=request)

        return {
            "button_text_dresses": "Shop Dresses",
            "button_link_products": product_list_url,
            "button_text_fabrics": "Shop Fabrics",
            "button_link_fabrics": material_list_url,
        }
