from decimal import Decimal

from django.db.models import Sum
from rest_framework.reverse import reverse

from core.choices import FABRIC_CARE_INSTRUCTIONS


class ProductUtils:
    @staticmethod
    def get_similar_products(product):

        from products.models import Products  # isort: skip

        similar_products = Products.objects.filter(
            categories=product.categories, status=product.status
        ).exclude(pk=product.pk)[:10]
        return similar_products

    @staticmethod
    def calculate_total_stock(product):

        total = product.variants.aggregate(Sum("stock"))["stock__sum"]
        return total if total else 0


class VariantUtils:
    @staticmethod
    def calculate_product_variant_final_price(variant):

        price = variant.product.price + variant.price_adjustment
        total_price = price - variant.product.discount

        return total_price.quantize(Decimal("0.00"))

    @staticmethod
    def calculate_sku_value(variant):

        sku_id = 10000

        category_code = variant.product.categories

        if variant.id:
            sku_id += variant.id

            color_code = str(variant.color).upper().replace(" ", "")
            size_code = str(variant.size).upper().replace(" ", "")

            value = f"MAC-PDT-{category_code}-{sku_id}-{color_code}-{size_code}"
            return value

    @staticmethod
    def get_stock_status(variant):
        if variant.stock <= 0:
            return "Product out of stock"
        elif variant.stock <= 7:
            return f"Only {variant.stock} left in stock"
        return "In stock"


class ProductDetailSerializerUtils:
    @staticmethod
    def get_fabric_care(product):
        spec = getattr(product, "specification", None) or getattr(
            product, "specification", None
        )

        if spec and spec.material_type:
            fabric_care = FABRIC_CARE_INSTRUCTIONS.get(
                spec.material_type, "Dry clean only."
            )
            return fabric_care
        return None

    @staticmethod
    def get_details(product):
        from products.serializers import ProductSpecificationSerializer  # isort : skip

        spec = getattr(product, "specification", None) or getattr(
            product, "specification", None
        )
        specification = None
        if not spec:
            return None
        specification = {
            "specification": ProductSpecificationSerializer(spec).data if spec else None
        }

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
    def get_reviews_urls(product, user_review, request):

        action_urls = {
            "review_create_url": (
                reverse(
                    "review_create",
                    kwargs={
                        "model_name": product.model_name,
                        "slug": product.slug,
                        "pk": product.id,
                    },
                    request=request,
                )
                if request
                else None
            ),
            "review_update_url": (
                reverse("review_update", kwargs={"pk": user_review.id}, request=request)
                if user_review and request
                else None
            ),
            "review_delete_url": (
                reverse("review_delete", kwargs={"pk": user_review.id}, request=request)
                if user_review and request
                else None
            ),
            "all_reviews": (
                reverse(
                    "all_single_item_review",
                    kwargs={
                        "model_name": product.model_name,
                        "slug": product.slug,
                        "pk": product.id,
                    },
                    request=request,
                )
                if request
                else None
            ),
        }

        return action_urls
