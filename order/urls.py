from django.urls import path

from order.views import (
    AddressView,
    CheckoutPreviewAPIView,
    CreateOrderFromCartView,
    OrderDetailsView,
    OrderListView,
)

urlpatterns = [
    path("preview/", CheckoutPreviewAPIView.as_view(), name="cart_preview"),
    path("address/", AddressView.as_view(), name="address_create"),
    path("address/<uuid:pk>/", AddressView.as_view(), name="address_update"),
    path("place_order/", CreateOrderFromCartView.as_view(), name="place_order"),
    path("/", OrderListView.as_view(), name="order_list"),
    path("<uuid:pk>/", OrderDetailsView.as_view(), name="order_details"),
]

# NOTE: Y
