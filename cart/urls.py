from django.urls import path
from cart.views import CartView,AddToCartView,UpdateCartItemView,RemoveCartItemView

urlpatterns = [
    path('',CartView.as_view(),name='cart'),
    path('add/',AddToCartView.as_view(),name='add-to-cart'),
    path('<str:pk>/update/',UpdateCartItemView.as_view(),name='cart'),
    path('<str:pk>/remove/',RemoveCartItemView.as_view(),name='cart'),   
    ]