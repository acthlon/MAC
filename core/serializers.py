from rest_framework import serializers
from rest_framework.reverse import reverse

from core.models import Banner, Category
from products.serializers import ProductCardSerializer
from review.serializers import ItemReviewSerializer
from utils.reviews.review import ReviewAnalyticsUtils


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)
    link = serializers.SerializerMethodField(read_only=True)

    def get_link(self, obj):

        request = self.context.get("request")
        item_list_url = (
            reverse("product_list", request=request)
            if obj.products and obj.target_model.model == "products"
            else reverse("material_list", request=request)
        )
        category_link = (f"{item_list_url}?categories={obj.name}" if obj.name else "#",)
        return category_link

    class Meta:
        model = Category
        fields = (
            "id",
            "target_model",
            "name",
            "image",
            "description",
            "slug",
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
        fields = ("id", "title", "subtitle", "image")


class HomePageSerializer(serializers.Serializer):
    average_rating = serializers.SerializerMethodField(read_only=True)
    total_customers = serializers.SerializerMethodField(read_only=True)
    satisfaction_rate = serializers.SerializerMethodField(read_only=True)
    hero_actions = serializers.SerializerMethodField(read_only=True)

    banners = BannerSeralizer(read_only=True, many=True)
    product_categories = CategorySerializer(read_only=True, many=True)
    material_categories = CategorySerializer(read_only=True, many=True)

    featured_products = ProductCardSerializer(read_only=True, many=True)
    new_arrivals = ProductCardSerializer(read_only=True, many=True)
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
