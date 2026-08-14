from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from core.choices import Status
from core.pagination import CatalogPagination
from core.permissions import IsAdminOrReadOnly
from materials.filters import MaterialsFilter
from materials.models import Materials
from materials.serializers import (
    MaterialDetailSerializer,
    MaterialListSerializer,
    MaterialSerializer,
)


class MaterialsListView(generics.ListAPIView):
    permission_classes = [
        AllowAny,
    ]

    serializer_class = MaterialListSerializer
    paginator_class = CatalogPagination

    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)

    filterset_class = MaterialsFilter
    search_fields = ("name", "description")
    ordering_fields = ("price", "quality_category")

    def get_queryset(self):

        user = self.request.user
        if user.is_staff:
            queryset = Materials.objects.select_related("categories").defer(
                "categories__image", "categories__icon"
            )
            return queryset
        else:
            queryset = (
                Materials.objects.filter(status=Status.ACTIVE)
                .select_related("categories")
                .defer("categories__icon")
            )
            return queryset

    def list(self, request, *args, **kwargs):
        from utils.core.core import CategoryUtils

        response = super().list(request, *args, **kwargs)

        categories = CategoryUtils.get_all_material_categories(self)

        response.data["all_material_categories"] = categories

        return response


class MaterialCreateView(generics.CreateAPIView):
    permission_classes = [
        IsAdminOrReadOnly,
    ]
    serializer_class = MaterialSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        request = self.request
        context["request"] = request
        return context


class MaterialUpdateDeleteView(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [
        IsAdminOrReadOnly,
    ]
    serializer_class = MaterialSerializer

    http_method_names = ["patch", "delete", "options"]

    def get_object(self):
        pk = self.kwargs.get("pk")

        material = get_object_or_404(Materials, pk=pk)
        return material


class MaterialDetailView(generics.RetrieveAPIView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = MaterialDetailSerializer

    def get_object(self):

        pk = self.kwargs.get("pk")
        queryset = (
            Materials.objects.filter(status=Status.ACTIVE)
            .prefetch_related("videos", "variants", "reviews")
            .select_related("specifications", "categories")
        )

        material = get_object_or_404(queryset, pk=pk)
        return material
