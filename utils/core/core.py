from core.choices import Status


class CategoryUtils:
    @staticmethod
    def get_all_material_categories(view):
        from core.models import Category
        from core.serializers import CategorySerializer

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
        from core.models import Category
        from core.serializers import CategorySerializer

        context = view.get_serializer_context()
        queryset = Category.objects.filter(
            status=Status.ACTIVE, target_model__model="products"
        )
        queryset_serialized = CategorySerializer(
            queryset, context=context, many=True
        ).data
        return queryset_serialized
