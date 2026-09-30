from django.urls import path

from order.views import (
    AddressAPIView,
    AddressUpdateDeleteAPIView,
    CheckoutPreviewAPIView,
    CreateOrderFromCartView,
    DeliveryMethodListCreateAPIView,
    DeliveryMethodManageAPIView,
    OrderDetailsView,
    OrderListView,
    TrackingOrderView,
)

urlpatterns = [
    path("checkout/", CheckoutPreviewAPIView.as_view(), name="cart_preview"),
    path("address/delivery/", AddressAPIView.as_view(), name="address_create"),
    path(
        "address/delivery/<uuid:pk>/manage/",
        AddressUpdateDeleteAPIView.as_view(),
        name="address_update_delete",
    ),
    path("place-order/", CreateOrderFromCartView.as_view(), name="place_order"),
    path("index/", OrderListView.as_view(), name="order_list"),
    path(
        "details/<str:order_number>/", OrderDetailsView.as_view(), name="order_details"
    ),
    path("track/<str:order_number>/", TrackingOrderView.as_view(), name="track_order"),
    path(
        "delivery-method/",
        DeliveryMethodListCreateAPIView.as_view(),
        name="delivery_method_list_create",
    ),
    path(
        "delivery-method/<str:pk>/manage/",
        DeliveryMethodManageAPIView.as_view(),
        name="delivery_method_detail_manage",
    ),
]
