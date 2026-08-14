from django.shortcuts import get_object_or_404
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from core.choices import Status
from core.pagination import CatalogPagination
from core.permissions import IsAdminOrReadOnly
from products.filters import ProductFilter
from products.models import Products
from products.serializers import (
    ProductDetailSerializer,
    ProductListSerializer,
    ProductSerializer,
)


class ProductsListView(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]

    paginator_class = CatalogPagination
    serializer_class = ProductListSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "quality_category"]

    def get_queryset(self):

        user = self.request.user
        if user.is_staff:
            queryset = Products.objects.select_related("categories").defer(
                "categories__image", "categories__icon"
            )
            return queryset

        elif not user.is_staff or not user.is_superuser:
            queryset = (
                Products.objects.filter(status=Status.ACTIVE)
                .select_related("categories")
                .defer("categories__image", "categories__icon")
            )
            return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        from utils.core.core import CategoryUtils  # isort: skip

        categories = CategoryUtils.get_all_product_categories(self)

        response.data["all_product_categories"] = categories

        return response


class ProductCreateView(generics.CreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductSerializer

    def get_serializer_context(self):

        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ProductUpdateDeleteView(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductSerializer

    http_method_names = ["patch", "delete", "options"]

    def get_object(self):

        pk = self.kwargs.get("pk")
        product = get_object_or_404(Products, pk=pk)
        return product


class ProductDetailsView(generics.RetrieveAPIView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = ProductDetailSerializer

    def get_object(self):

        pk = self.kwargs.get("pk")
        queryset = (
            Products.objects.filter(status="ACTIVE")
            .prefetch_related("variants", "videos", "reviews")
            .select_related("specification", "categories")
        )

        product = get_object_or_404(queryset, pk=pk)
        return product
