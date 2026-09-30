import datetime

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from core.choices import MAX_FILE_SIZE
from core.models import Category
from core.serializers import BaseCatalogCardSerializer
from products.models import (
    ProductImages,
    Products,
    ProductSpecification,
    ProductVariant,
    ProductVideo,
)
from review.serializers import ItemReviewSerializer


class ProductSpecificationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    material_type_display = serializers.CharField(
        source="get_material_type_display", read_only=True
    )

    class Meta:
        model = ProductSpecification
        fields = (
            "id",
            "product_line",
            "weight",
            "material_type",
            "material_type_display",
            "key_features",
        )
        read_only_fields = ("id",)


class ProductImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    def validate_image(self, value):
        if value and value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("Image size must be less than 5MB.")
        return value

    class Meta:
        model = ProductImages
        fields = ("id", "image", "display_order", "is_primary")


class ProductVariantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    size_display = serializers.CharField(source="get_size_display", read_only=True)
    color_display = serializers.CharField(source="get_color_display", read_only=True)
    stock_status = serializers.CharField(read_only=True, source="get_stock_status")
    final_price = serializers.ReadOnlyField(source="calculate_variant_final_price")
    images = ProductImageSerializer(many=True, required=False)

    def validate(self, data):
        if "price_adjustment" in data and data.get("price_adjustment") is not None:
            if data["price_adjustment"] < 0:
                raise serializers.ValidationError(
                    {"price_adjustment": "Price adjustment cannot be negative."}
                )
        if data.get("stock") is not None and data.get("stock") < 0:
            raise serializers.ValidationError({"stock": "Stock cannot be negative."})
        return data

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "size",
            "size_display",
            "color",
            "color_display",
            "stock",
            "stock_status",
            "sku",
            "price_adjustment",
            "final_price",
            "status",
            "images",
        )
        read_only_fields = ("sku",)


class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = (
            "id",
            "video",
            "thumbnail",
            "display_order",
        )


class ProductCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "status")


class ProductWriteSerializer(serializers.ModelSerializer):
    specification = ProductSpecificationSerializer(required=False)
    variants = ProductVariantSerializer(many=True, required=False)
    videos = ProductVideoSerializer(many=True, required=False)
    item_detail_url = serializers.SerializerMethodField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    percent_discount = serializers.ReadOnlyField(source="calculate_percent_discount")
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(target_model__model="products"), required=False
    )

    def get_item_detail_url(self, obj):
        request = self.context.get("request")
        url = reverse(
            "product_details", kwargs={"slug": obj.slug, "pk": obj.id}, request=request
        )
        return url

    def validate(self, data):
        request = self.context.get("request")
        request_method = request.method if request else None

        if request_method in ["PUT", "PATCH", "POST"]:
            if "price" in data and data.get("price") <= 0:
                raise serializers.ValidationError(
                    {"price": "Price must be greater than 0"}
                )

            if (
                "discount" in data
                and data.get("discount") is not None
                and data.get("discount") < 0
            ):
                raise serializers.ValidationError(
                    {"discount": "Discount cannot be negative"}
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request and hasattr(request, "user") else None

        spec_data = validated_data.pop("specification", None)
        variants_data = validated_data.pop("variants", [])
        videos_data = validated_data.pop("videos", [])

        product = Products.objects.create(**validated_data, user=user)

        if spec_data:
            ProductSpecification.objects.create(product=product, user=user, **spec_data)

        for video_data in videos_data:
            ProductVideo.objects.create(product=product, **video_data)

        for variant_data in variants_data:
            images_data = variant_data.pop("images", [])
            variant = ProductVariant.objects.create(product=product, **variant_data)
            for img_data in images_data:
                ProductImages.objects.create(variant=variant, **img_data)

        return product

    @transaction.atomic
    def update(self, instance, validated_data):

        spec_data = validated_data.pop("specification", None)
        variants_data = validated_data.pop("variants", None)
        videos_data = validated_data.pop("videos", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if spec_data is not None:
            ProductSpecification.objects.update_or_create(
                product=instance, defaults=spec_data
            )

        if videos_data is not None:
            for video_data in videos_data:
                video_id = video_data.pop("id", None)
                video_obj = (
                    ProductVideo.objects.get(id=video_id, product=instance)
                    if video_id
                    else None
                )

                if video_obj:
                    for field, value in video_data.items():
                        if hasattr(video_obj, field):
                            setattr(video_obj, field, value)
                            video_obj.save(update_fields=[field])
                        else:
                            raise serializers.ValidationError(
                                {field: "Field does not exist"}
                            )

                else:
                    ProductVideo.objects.create(product=instance, user=user**video_data)

        if variants_data is not None:
            for variant_data in variants_data:
                variant_id = variant_data.pop("id", None)
                images_data = variant_data.pop("images", [])

                if variant_id:
                    ProductVariant.objects.filter(
                        id=variant_id, product=instance
                    ).update(**variant_data)
                    variant = ProductVariant.objects.get(
                        id=variant_id, product=instance
                    )
                    variant.save()
                else:
                    variant = ProductVariant.objects.create(
                        product=instance, **variant_data
                    )

                for img_data in images_data:
                    img_data_id = img_data.pop("id", None)
                    image_obj = (
                        ProductImages.objects.get(id=img_data_id, variant=variant)
                        if img_data_id
                        else None
                    )

                    if image_obj:
                        for field, value in img_data.items():
                            if hasattr(image_obj, field):
                                setattr(image_obj, field, value)
                                image_obj.save(update_fields=[field])

                            else:
                                raise serializers.ValidationError(
                                    {field: "Field does not exist"}
                                )
                    else:
                        ProductImages.objects.create(variant=variant, **img_data)
        return instance

        # NOTE: update material serializers too.

    class Meta:
        model = Products
        fields = (
            "id",
            "name",
            "description",
            "price",
            "slug",
            "discount",
            "percent_discount",
            "item_detail_url",
            "quality_category",
            "status",
            "categories",
            "specification",
            "variants",
            "videos",
        )


class ProductInfoSerializer(serializers.ModelSerializer):
    discounted_price = serializers.DecimalField(
        source="calculate_discounted_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
        required=False,
    )
    total_stock = serializers.IntegerField(
        source="calculate_total_stock", read_only=True, required=False
    )
    percent_discount = serializers.ReadOnlyField(
        source="calculate_percent_disount", required=False
    )
    is_new_arrival = serializers.SerializerMethodField(read_only=True, required=False)
    average_rating = serializers.ReadOnlyField(
        source="calculate_average_rating", required=False
    )
    review_count = serializers.IntegerField(
        source="calculate_review_count", read_only=True, required=False
    )
    category = serializers.CharField(
        source="categories.name", read_only=True, required=False
    )

    def get_is_new_arrival(self, obj):
        # 1. Figure out what the date was exactly 7 days ago
        seven_days_ago = timezone.now() - datetime.timedelta(days=7)
        is_new = obj.created_at >= seven_days_ago
        return is_new

    class Meta:
        model = Products
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "discount",
            "discounted_price",
            "total_stock",
            "percent_discount",
            "quality_category",
            "category",
            "is_new_arrival",
            "average_rating",
            "review_count",
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    product_info = serializers.SerializerMethodField()
    variant_details = serializers.SerializerMethodField()
    grouped_variant_sizes = serializers.SerializerMethodField()
    videos = ProductVideoSerializer(many=True, read_only=True)
    details = serializers.SerializerMethodField()
    fabric_care = serializers.SerializerMethodField()
    reviews_data = serializers.SerializerMethodField()
    similar_products = BaseCatalogCardSerializer(
        source="get_similar_products", many=True
    )
    add_to_cart_url = serializers.SerializerMethodField(read_only=True)

    def get_add_to_cart_url(self, obj):
        request = self.context.get("request")
        url = reverse("add_to_cart", request=request)
        return url

    def get_product_info(self, obj):

        product = ProductInfoSerializer(obj, context=self.context).data
        return product

    def get_variant_details(self, obj):

        request = self.context.get("request")
        variant_list = []
        for var in obj.variants.all():
            variant_details = ProductVariantSerializer(var, context=self.context).data

            variant_list.append(variant_details)
        return variant_list

    def get_grouped_variant_sizes(self, obj):
        variant_list = self.get_variant_details(obj)
        from utils.products.product import ProductDetailSerializerUtils  # isort: skip

        return ProductDetailSerializerUtils.get_grouped_variant_sizes(variant_list)

    def get_details(self, obj):
        from utils.products.product import ProductDetailSerializerUtils  # isort: skip

        return ProductDetailSerializerUtils.get_details(obj)

    def get_fabric_care(self, obj):
        from utils.products.product import ProductDetailSerializerUtils  # isort: skip

        return ProductDetailSerializerUtils.get_fabric_care(obj)

    def get_reviews_data(self, obj):
        from utils.products.product import ProductDetailSerializerUtils  # isort: skip

        request = self.context.get("request")
        user = request.user
        user_review = None

        if user and user.is_authenticated:
            user_review = user.reviews.filter(
                object_id=obj.pk, purchase_verified=True
            ).first()

        action_urls = ProductDetailSerializerUtils.get_reviews_urls(
            obj, user_review, request
        )

        reviews_qs = obj.reviews.filter(purchase_verified=True).select_related("user")[
            :3
        ]
        reviews_qs_serialized = ItemReviewSerializer(reviews_qs, many=True).data
        reviews_list = {"review": reviews_qs_serialized}

        reviews = {
            "action_url": action_urls,
            "average_rating": obj.calculate_average_rating,
            "review_count": obj.calculate_review_count,
            "items": reviews_list,
        }
        return reviews

    class Meta:
        model = Products
        fields = (
            "add_to_cart_url",
            "product_info",
            "variant_details",
            "grouped_variant_sizes",
            "videos",
            "details",
            "fabric_care",
            "reviews_data",
            "similar_products",
        )
