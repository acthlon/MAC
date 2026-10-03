import datetime

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from core.choices import MAX_FILE_SIZE
from core.models import Category
from core.serializers import BaseCatalogCardSerializer
from materials.models import (
    MaterialImages,
    Materials,
    MaterialSpecification,
    MaterialVariant,
    MaterialVideo,
)
from review.serializers import ItemReviewSerializer


class MaterialSpecificationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    material_type_display = serializers.CharField(
        source="get_material_type_display", read_only=True
    )

    class Meta:
        model = MaterialSpecification
        fields = (
            "id",
            "width",
            "width",
            "thread_count",
            "weight",
            "pattern",
            "material_type",
            "material_type_display",
            "key_features",
        )
        read_only_fields = ("id",)


class MaterialImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    def validate_image(self, value):
        if value and value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("Image size must be less than 5MB.")
        return value

    class Meta:
        model = MaterialImages
        fields = ("id", "image", "display_order", "is_primary")


class MaterialVariantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    color_display = serializers.CharField(source="get_color_display", read_only=True)
    stock_status = serializers.CharField(read_only=True, source="get_stock_status")
    final_price = serializers.ReadOnlyField(source="calculate_variant_discounted_price")
    images = MaterialImageSerializer(many=True, required=False)

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
        model = MaterialVariant
        fields = (
            "id",
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


class MaterialVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialVideo
        fields = (
            "id",
            "video",
            "thumbnail",
            "display_order",
        )


class MaterialCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("name", "status")


class MaterialWriteSerializer(serializers.ModelSerializer):
    variants = MaterialVariantSerializer(many=True, required=False)
    videos = MaterialVideoSerializer(many=True, required=False)
    item_detail_url = serializers.SerializerMethodField(read_only=True)
    slug = serializers.SlugField(read_only=True)
    percent_discount = serializers.ReadOnlyField(source="calculate_percent_discount")
    categories = MaterialCategoriesSerializer()

    def get_item_detail_url(self, obj):
        request = self.context.get("request")
        url = reverse(
            "material_details", kwargs={"slug": obj.slug, "pk": obj.id}, request=request
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

        specification_data = validated_data.pop("specification", None)
        variants_data = validated_data.pop("variants", [])
        videos_data = validated_data.pop("videos", [])

        material = Materials.objects.create(**validated_data, user=user)

        if specification_data:
            MaterialSpecification.objects.create(
                material=material, **specification_data
            )

        for video_data in videos_data:
            MaterialVideo.objects.create(material=material, **video_data)

        for variant_data in variants_data:
            images_data = variant_data.pop("images", [])
            variant = MaterialVariant.objects.create(material=material, **variant_data)
            for img_data in images_data:
                MaterialImages.objects.create(variant=variant, **img_data)

        return material

    @transaction.atomic
    def update(self, instance, validated_data):

        specification_data = validated_data.pop("specification", None)
        variants_data = validated_data.pop("variants", None)
        videos_data = validated_data.pop("videos", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if specification_data is not None:
            MaterialSpecification.objects.update_or_create(
                material=instance, defaults=specification_data
            )

        if videos_data is not None:
            for video_data in videos_data:
                video_id = video_data.pop("id", None)
                video_obj = (
                    MaterialVideo.objects.filter(id=video_id, material=instance).first()
                    if video_id
                    else None
                )

                if video_obj:
                    for field, value in video_data.items():
                        if hasattr(video_obj, field):
                            setattr(video_obj, field, value)
                        else:
                            raise serializers.ValidationError(
                                {"message": "Field does not exist"}
                            )
                    video_obj.save()
                else:
                    MaterialVideo.objects.create(material=instance, **video_data)

        if variants_data is not None:
            for variant_data in variants_data:
                variant_id = variant_data.pop("id", None)
                images_data = variant_data.pop("images", [])

                if variant_id:
                    MaterialVariant.objects.filter(
                        id=variant_id, material=instance
                    ).update(**variant_data)
                    variant = MaterialVariant.objects.filter(
                        id=variant_id, material=instance
                    ).first()
                    if variant:
                        variant.save()
                else:
                    variant = MaterialVariant.objects.create(
                        material=instance, **variant_data
                    )

                if variant:
                    for img_data in images_data:
                        img_data_id = img_data.pop("id", None)
                        img_obj = (
                            MaterialImages.objects.filter(
                                id=img_data_id, variant=variant
                            ).first()
                            if img_data_id
                            else None
                        )

                        if img_obj:
                            for field, value in img_data.items():
                                if hasattr(img_obj, field):
                                    setattr(img_obj, field, value)
                                else:
                                    raise serializers.ValidationError(
                                        {"message": "Field does not exist"}
                                    )
                            img_obj.save()
                        else:
                            MaterialImages.objects.create(variant=variant, **img_data)

        return instance

    class Meta:
        model = Materials
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
            "variants",
            "videos",
        )


class MaterialInfoSerializer(serializers.ModelSerializer):
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
        model = Materials
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


class MaterialDetailSerializer(serializers.ModelSerializer):
    material_info = serializers.SerializerMethodField()
    variant_details = serializers.SerializerMethodField()
    videos = MaterialVideoSerializer(many=True, read_only=True)
    details = serializers.SerializerMethodField()
    fabric_care = serializers.SerializerMethodField()
    reviews_data = serializers.SerializerMethodField()
    similar_materials = BaseCatalogCardSerializer(
        source="get_similar_materials", many=True
    )
    add_to_cart_url = serializers.SerializerMethodField(read_only=True)

    def get_add_to_cart_url(self, obj):
        request = self.context.get("request")
        url = reverse("add_to_cart", request=request)
        return url

    def get_material_info(self, obj):

        material = MaterialInfoSerializer(obj, context=self.context).data
        return material

    def get_variant_details(self, obj):

        request = self.context.get("request")
        variant_list = []
        for var in obj.variants.all():
            variant_details = MaterialVariantSerializer(var, context=self.context).data

            variant_list.append(variant_details)
        return variant_list

    def get_details(self, obj):
        from utils.materials.material import MaterialDetailSerializerUtils  # isort: skip

        return MaterialDetailSerializerUtils.get_details(obj)

    def get_fabric_care(self, obj):
        from utils.materials.material import MaterialDetailSerializerUtils  # isort: skip

        return MaterialDetailSerializerUtils.get_fabric_care(obj)

    def get_reviews_data(self, obj):
        from utils.materials.material import MaterialDetailSerializerUtils  # isort: skip

        request = self.context.get("request")
        user = request.user
        user_review = None

        if user and user.is_authenticated:
            user_review = user.reviews.filter(
                object_id=obj.pk, purchase_verified=True
            ).first()

        action_urls = MaterialDetailSerializerUtils.get_reviews_urls(
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
        model = Materials
        fields = (
            "add_to_cart_url",
            "material_info",
            "reviews_data",
            "variant_details",
            "videos",
            "details",
            "fabric_care",
            "similar_materials",
        )
