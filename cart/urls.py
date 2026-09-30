from django.urls import path

from cart.views import AddToCartView, CartItemUpdateDeleteView, CartView

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    path("add/", AddToCartView.as_view(), name="add_to_cart"),
    path(
        "<str:pk>/manage/",
        CartItemUpdateDeleteView.as_view(),
        name="cart_update_delete",
    ),
]
