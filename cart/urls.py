from django.urls import path

from cart.views import AddToCartView, CartView, RemoveCartItemView, UpdateCartItemView

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("add/", AddToCartView.as_view(), name="add_to_cart"),
    path("<str:pk>/update/", UpdateCartItemView.as_view(), name="cart_update"),
    path("<str:pk>/remove/", RemoveCartItemView.as_view(), name="cart_delete"),
]
