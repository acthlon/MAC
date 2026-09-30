from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from cart.models import Cart
from core.permissions import IsAdminOrReadOnly
from order.models import (
    Address,
    DeliveryMethod,
    Order,
)
from order.serializers import (
    AddressSerializer,
    CheckoutPreviewSerializer,
    CreateOrderFromCartSerializer,
    DeliveryMethodSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    TrackingOrderSerializer,
)


class AddressAPIView(generics.CreateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = AddressSerializer


class AddressUpdateDeleteAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = AddressSerializer

    http_method_names = ["patch", "delete", "options"]

    def get_object(self):

        pk = self.kwargs.get("pk")
        user = self.request.user
        address = get_object_or_404(Address, id=pk, user=user)
        return address


class DeliveryMethodListCreateAPIView(generics.CreateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = DeliveryMethodSerializer




class DeliveryMethodManageAPIView(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [
        IsAdminOrReadOnly,
    ]
    serializer_class = DeliveryMethodSerializer

    def get_object(self):
        id = self.kwargs.get("pk")
        method = get_object_or_404(DeliveryMethod, id=id)
        return method


class CheckoutPreviewAPIView(generics.RetrieveAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CheckoutPreviewSerializer

    def get_object(self):
        request = self.request
        user = request.user

        cart = (
            Cart.objects.filter(user=user)
            .prefetch_related(
                "items",
                "items__content_object",
                "items__content_type",
                # "items__content_object__images"
            )
            .first()
        )

        return cart


class CreateOrderFromCartView(generics.CreateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CreateOrderFromCartSerializer


class OrderListView(generics.ListAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = OrderListSerializer

    def get_queryset(self):

        user = self.request.user
        items = (
            Order.objects.filter(user=user)
            .prefetch_related("items")
            .order_by("-created_at")
        )
        return items


class OrderDetailsView(generics.RetrieveAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = OrderDetailSerializer

    def get_object(self):

        user = self.request.user
        order_number = self.kwargs.get("order_number")

        order = get_object_or_404(Order, order_number=order_number, user=user)
        return order


class TrackingOrderView(generics.RetrieveAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = TrackingOrderSerializer

    def get_object(self):
        user = self.request.user
        order_number = self.kwargs.get("order_number")
        order = get_object_or_404(Order, user=user, order_number=order_number)

        return order
