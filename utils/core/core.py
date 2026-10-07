from core.choices import Status


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
