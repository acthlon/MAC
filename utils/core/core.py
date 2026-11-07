from itertools import zip_longest

from core.choices import Status
from materials.models import Materials
from products.models import Products


class CategoryUtils:
    @staticmethod
    def get_all_material_categories(view):
        from core.models import Category  # isort: skip
        from core.serializers import CategorySerializer  # isort: skip

        context = view.get_serializer_context()
        queryset = Category.objects.filter(
            status=Status.ACTIVE, target_model__model="materials"
        )
        queryset_serialized = CategorySerializer(
            queryset, context=context, many=True
        ).data
        return queryset_serialized

    @staticmethod
    def get_all_product_categories(view):
        from core.models import Category  # isort: skip
        from core.serializers import CategorySerializer  # isort: skip

        context = view.get_serializer_context()
        queryset = Category.objects.filter(
            status=Status.ACTIVE, target_model__model="products"
        )
        queryset_serialized = CategorySerializer(
            queryset, context=context, many=True
        ).data
        return queryset_serialized


class CatalogUtils:
    @staticmethod
    def get_catalog_item(item_obj):
        variant_obj = getattr(item_obj, "content_object", None)
        if not variant_obj:
            return None

        # ProductVariantSize -> variant.product
        if hasattr(variant_obj, "variant") and hasattr(variant_obj.variant, "product"):
            return variant_obj.variant.product

        # ProductVariant -> product, or MaterialVariant -> material
        if hasattr(variant_obj, "product"):
            return variant_obj.product
        if hasattr(variant_obj, "material"):
            return variant_obj.material

        # If it's directly Products or Materials
        if hasattr(variant_obj, "name"):
            return variant_obj

        return None

    @staticmethod
    def get_new_arrivals(limit: int = 10):
        half = limit // 2

        product_new_arrivals = list(
            Products.objects.filter(status=Status.ACTIVE)
            .select_related("categories")
            .order_by("-created_at")[:limit]
        )
        material_new_arrivals = list(
            Materials.objects.filter(status=Status.ACTIVE)
            .select_related("categories")
            .order_by("-created_at")[:limit]
        )

        product_items = product_new_arrivals[:half]
        material_items = material_new_arrivals[:half]

        # If one category has fewer than 4 items, backfill from the other
        if len(product_items) < half:
            needed = half - len(product_items)
            material_items.extend(material_new_arrivals[half : half + needed])
        elif len(material_items) < half:
            needed = half - len(material_items)
            product_items.extend(product_new_arrivals[half : half + needed])

        interleaved = []
        for product, material in zip_longest(product_items, material_items):
            if product:
                interleaved.append(product)
            if material:
                interleaved.append(material)

        return interleaved[:limit]

    @staticmethod
    def get_featured_items(limit: int = 10):
        half = limit // 2

        featured_products = list(
            Products.objects.filter(status=Status.ACTIVE, discount__gt=15000)
            .select_related("categories")
            .order_by("-created_at")[:limit]
        )
        featured_materials = list(
            Materials.objects.filter(status=Status.ACTIVE, discount__gt=15000)
            .select_related("categories")
            .order_by("-created_at")[:limit]
        )

        product_items = featured_products[:half]
        material_items = featured_materials[:half]

        # If one category has fewer than 4 items, backfill from the other
        if len(product_items) < half:
            needed = half - len(product_items)
            material_items.extend(featured_materials[half : half + needed])
        elif len(material_items) < half:
            needed = half - len(material_items)
            product_items.extend(featured_products[half : half + needed])

        interleaved = []
        for product, material in zip_longest(product_items, material_items):
            if product:
                interleaved.append(product)
            if material:
                interleaved.append(material)

        return interleaved[:limit]
