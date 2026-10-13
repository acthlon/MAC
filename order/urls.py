from django.urls import path

from order.views import (
    AddressAPIView,
    AddressUpdateDeleteAPIView,
    CreateOrderFromCartView,
    DeliveryMethodListCreateAPIView,
    DeliveryMethodManageAPIView,
    OrderDetailsView,
    OrderListView,
    TrackingOrderView,
)

urlpatterns = [
    path("address/delivery/", AddressAPIView.as_view(), name="address_create"),
    path(
        "address/delivery/<uuid:pk>/manage/",
        AddressUpdateDeleteAPIView.as_view(),
        name="address_update_delete",
    ),
    path("place-order/", CreateOrderFromCartView.as_view(), name="place_order"),
    path("index/", OrderListView.as_view(), name="order_list"),
    path(
        "<str:order_number>/details/", OrderDetailsView.as_view(), name="order_details"
    ),
    path("track/<str:tracking_id>/", TrackingOrderView.as_view(), name="track_order"),
    path(
        "delivery-method/",
        DeliveryMethodListCreateAPIView.as_view(),
        name="create_listdelivery_method",
    ),
    path(
        "delivery-method/<str:pk>/manage/",
        DeliveryMethodManageAPIView.as_view(),
        name="manage_delivery_method_detail",
    ),
]
