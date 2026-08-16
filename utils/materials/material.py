from decimal import Decimal

from django.db.models import Sum
from rest_framework.reverse import reverse

from core.choices import FABRIC_CARE_INSTRUCTIONS


class VariantUtils:
    @staticmethod
    def calculate_sku_value(variant):

        sku_id = 10000
        category_code = variant.material.categories

        if variant.id:
            sku_id += variant.id

            color_code = str(variant.color).upper().replace(" ", "")

            value = f"MAC-MTL-{category_code}-{sku_id}-{color_code}"
            return value

    @staticmethod
    def calculate_material_variant_final_price(variant):

        price = variant.material.price + variant.price_adjustment
        total_price = price - variant.material.discount
        # return total_price
        return total_price.quantize(Decimal("0.00"))

    @staticmethod
    def get_stock_status(variant):
        if variant.stock <= 0:
            return "Material out of stock"
        elif variant.stock <= 7:
            return f"Only {variant.stock} left in stock"
        return "In stock"


class MaterialUtils:
    @staticmethod
    def get_similar_materials(material):

        from materials.models import Materials  # isort: skip

        similar_materials = Materials.objects.filter(
            categories=material.categories, status=material.status
        ).exclude(pk=material.id)[:10]

        return similar_materials

    @staticmethod
    def calculate_total_stock(material):

        total = material.variants.aggregate(Sum("stock"))["stock__sum"]
        return total if total else 0


class MaterialDetailSerializerUtils:
    @staticmethod
    def get_fabric_care(material):
        spec = getattr(material, "material_spec", None)

        if spec and spec.material_type:
            fabric_care = FABRIC_CARE_INSTRUCTIONS.get(
                spec.material_type, "Dry clean only."
            )
            return fabric_care
        return None

    @staticmethod
    def get_details(material):
        from materials.serializers import (
            MaterialSpecificationSerializer,
        )  # isort : skip

        spec = getattr(material, "material_spec", None)
        specification = None
        if not spec:
            return None
        specification = {"specification": MaterialSpecificationSerializer(spec).data}

        details = {
            "key_features": spec.key_features,
            "specification": specification,
        }
        return details

    @staticmethod
    def get_grouped_variant_sizes(variant_list):
        grouped_variant_sizes = {}
        available_colors = []

        for variant in variant_list:
            color_key = variant.get("color")

            if color_key not in available_colors:
                available_colors.append(color_key)

            if color_key not in grouped_variant_sizes:
                grouped_variant_sizes[color_key] = []

            grouped_variant_sizes[color_key].append(
                {
                    "size_display": variant.get("size_display"),
                    "size": variant.get("size"),
                    "stock": variant.get("stock"),
                }
            )
        return grouped_variant_sizes

    @staticmethod
    def get_reviews_urls(material, user_review, request):

        action_urls = {
            "review_create_url": (
                reverse(
                    "review_create",
                    kwargs={
                        "model_name": material.model_name,
                        "slug": material.slug,
                        "pk": material.id,
                    },
                    request=request,
                )
                if request
                else None
            ),
            "review_update_delete_url": (
                reverse(
                    "review_update_delete",
                    kwargs={"pk": user_review.id},
                    request=request,
                )
                if user_review and request
                else None
            ),
            "all_reviews": (
                reverse(
                    "all_single_item_review",
                    kwargs={
                        "model_name": material.model_name,
                        "slug": material.slug,
                        "pk": material.id,
                    },
                    request=request,
                )
                if request
                else None
            ),
        }

        return action_urls
