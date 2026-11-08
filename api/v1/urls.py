from django.urls import include, path

from core.views import HomePageAPIView, NewArrivalsAPIView
from order.views import CheckoutPreviewAPIView

urlpatterns = [
    path("auth/", include("accounts.urls")),
    path("products/", include("products.urls")),
    path("materials/", include("materials.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("order.urls")),
    path("checkout/", CheckoutPreviewAPIView.as_view(), name="cart_preview"),
    path("payments/", include("payments.urls")),
    path("reviews/", include("review.urls")),
    path("home/", HomePageAPIView.as_view(), name="home"),
    path("new-arrivals/", NewArrivalsAPIView.as_view(), name="new_arrivals"),
]
