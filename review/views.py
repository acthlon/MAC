from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.reverse import reverse

from core.pagination import ReviewPagination
from core.permissions import IsOwnerOrReadOnly
from review.models import Reviews
from review.serializers import (
    ReviewListSerializer,
    ReviewWriteSerializer,
)
from utils.reviews.review import ReviewUtils


class ReviewCreateView(generics.CreateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = ReviewWriteSerializer

    def get_serializer_context(self):

        context = super().get_serializer_context()

        context.update(
            {
                "item_id": self.kwargs.get("pk"),
                "slug": self.kwargs.get("slug"),
                "model_name": self.kwargs.get("model_name", "").lower(),
            }
        )

        return context


class ReviewListByItem(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ReviewListSerializer
    pagination_class = ReviewPagination

    def get_queryset(self):

        pk = self.kwargs.get("pk")
        model_name = self.kwargs.get("model_name")

        try:
            content_type = ContentType.objects.get(model=model_name.lower())
        except ContentType.DoesNotExist:
            raise NotFound(detail="Wrong model type")

        reviews = (
            Reviews.objects.filter(
                purchase_verified=True, object_id=pk, content_type=content_type
            )
            .select_related("user")
            .only(
                "comment",
                "rating",
                "created_at",
                "updated_at",
                "user",
                "user__profile_image",
                "user__first_name",
                "user__last_name",
            )
            .order_by("-created_at")
        )
        return reviews

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        pk = self.kwargs.get("pk")
        model_name = self.kwargs.get("model_name")
        slug = self.kwargs.get("slug")

        link_name = (
            "material_details" if model_name == "materials" else "product_details"
        )
        item_detail_url = reverse(
            link_name,
            request=request,
            kwargs={
                "pk": pk,
                "slug": slug,
            },
        )
        try:
            content_type = ContentType.objects.get(model=model_name)
            item_average_rating = ReviewUtils.calculate_item_average_rating(
                pk, content_type
            )

        except ContentType.DoesNotExist:
            item_average_rating = 0.0

        response.data = {
            "item_detail_url": item_detail_url,
            "item_average_rating": item_average_rating,
            **response.data,
        }
        return response


class ReviewUpdateDeleteView(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [
        IsOwnerOrReadOnly,
    ]
    serializer_class = ReviewWriteSerializer

    def get_object(self):

        pk = self.kwargs.get("pk")
        review = get_object_or_404(Reviews, pk=pk)
        return review
