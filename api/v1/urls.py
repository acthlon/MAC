from django.urls import include, path

urlpatterns = [
    path("auth/", include("accounts.urls")),
    path("products/", include("products.urls")),
    path("materials/", include("materials.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("order.urls")),
    path("checkout/", include("order.urls")),
    path("payments/", include("payments.urls")),
    path("reviews/", include("review.urls")),
    path("home/", include("core.urls")),
]
