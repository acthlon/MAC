from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.choices import Status
from core.serializers import HomePageSerializer
from products.models import Products
from review.models import Reviews

from .models import Banner, Category


class HomePageAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = HomePageSerializer

    def get(self, request):
        banners = Banner.objects.filter(status=Status.ACTIVE).order_by("display_order")
        categories = (
            Category.objects.filter(status=Status.ACTIVE)
            .select_related("target_model")
            .order_by("display_order")
        )
        featured_products = Products.objects.filter(
            status=Status.ACTIVE, discount__gt=15000
        ).order_by("-created_at")[:8]
        new_arrivals = Products.objects.filter(status=Status.ACTIVE).order_by(
            "-created_at"
        )[:8]
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
            "featured_products": featured_products,
            "reviews": reviews,
            "product_categories": product_categories,
            "material_categories": material_categories,
            "new_arrivals": new_arrivals,
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)
