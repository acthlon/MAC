from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from cart.models import Cart, CartItem
from cart.serializers import CartItemWriteSerializer, CartSerializer


class CartView(generics.RetrieveAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CartSerializer

    def get_object(self):

        user = self.request.user
        cart = Cart.objects.prefetch_related("items").get_or_create(user=user)
        return cart


class AddToCartView(generics.CreateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CartItemWriteSerializer


class CartItemUpdateDeleteView(generics.UpdateAPIView, generics.DestroyAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CartItemWriteSerializer

    http_method_names = ["patch", "delete", "options"]

    def get_object(self):

        user = self.request.user
        pk = self.kwargs.get("pk")

        cart_item = get_object_or_404(CartItem, id=pk, cart__user=user)
        return cart_item
