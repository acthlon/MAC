from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from cart.models import Cart, CartItem
from cart.serializers import CartItemWriteSerializer, CartSerializer


class CartView(generics.RetrieveAPIView):
    # you will need to add guest logic for this at the frontend before you can make use of AllowAny.

    permission_classes = [
        IsAuthenticated,
    ]  # NOTE: change to IsAuthentcated
    serializer_class = CartSerializer

    def get_object(self):

        user = self.request.user
        cart = get_object_or_404(Cart.objects.prefetch_related("items"), user=user)
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
