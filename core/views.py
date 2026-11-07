from datetime import timedelta
from itertools import zip_longest

from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.choices import Status
from core.pagination import CatalogPagination
from core.serializers import BaseCatalogCardSerializer, HomePageSerializer
from materials.filters import MaterialsFilter
from materials.models import Materials
from products.filters import ProductFilter
from products.models import Products
from review.models import Reviews

from .models import Banner, Category


class HomePageAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = HomePageSerializer

    def get(self, request):
        from utils.core.core import CatalogUtils  # isort : skip

        banners = Banner.objects.filter(status=Status.ACTIVE).order_by("display_order")
        categories = (
            Category.objects.filter(status=Status.ACTIVE)
            .select_related("target_model")
            .order_by("display_order")
        )
        featured_items = CatalogUtils.get_featured_items()

        new_arrivals = CatalogUtils.get_new_arrivals()
        reviews = (
            Reviews.objects.filter(purchase_verified=True)
            .select_related("user")
            .only(
                "comment",
                "rating",
                "user",
                "user__profile_image",
                "user__first_name",
                "user__last_name",
            )[:8]
        )

        # Separate categories based on their target model
        product_categories = [
            c
            for c in categories
            if c.target_model and c.target_model.model == "products"
        ]

        material_categories = [
            c
            for c in categories
            if c.target_model and c.target_model.model == "materials"
        ]

        data = {
            "banners": banners,
            "categories": categories,
            "featured_items": featured_items,
            "reviews": reviews,
            "product_categories": product_categories,
            "material_categories": material_categories,
            "new_arrivals": new_arrivals,
        }

        serializer = self.serializer_class(data, context={"request": request})
        return Response(serializer.data)


class NewArrivalsAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = BaseCatalogCardSerializer
    pagination_class = CatalogPagination

    def get(self, request, *args, **kwargs):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        product_qs = (
            Products.objects.filter(
                status=Status.ACTIVE,
                # created_at__gte =thirty_days_ago
            )
            .select_related("categories")
            .order_by("-created_at")
        )
        material_qs = (
            Materials.objects.filter(
                status=Status.ACTIVE,
                # created_at__gte =thirty_days_ago
            )
            .select_related("categories")
            .order_by("-created_at")
        )

        filtered_products = ProductFilter(
            request.GET, queryset=product_qs, request=request
        ).qs
        if request.GET.get("sizes"):
            filtered_materials = Materials.objects.none()
        else:
            filtered_materials = MaterialsFilter(
                request.GET, queryset=material_qs, request=request
            ).qs

        # 3. HIGH EFFICIENCY FIX: Cap the memory load (e.g. top 100 of each)
        # "New arrivals" only cares about recent items, not your entire archive
        products_list = list(filtered_products[:100])
        materials_list = list(filtered_materials[:100])

        # 4. Interleave: [Product1, Material1, Product2, Material2, ...]
        # This gives a consistent 50/50 mix across all pages with NO duplicate bugs
        interleaved = []
        for product, material in zip_longest(products_list, materials_list):
            if product:
                interleaved.append(product)
            if material:
                interleaved.append(material)

        # 3. Paginate manually using CatalogPagination
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(interleaved, request, view=self)

        if page is not None:
            serializer = self.serializer_class(
                page, many=True, context={"request": request}
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = self.serializer_class(
            interleaved, many=True, context={"request": request}
        )
        return Response(serializer.data)
