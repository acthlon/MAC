from django.urls import path

from products.views import (
    ProductCreateView,
    ProductDetailsView,
    ProductsListView,
    ProductUpdateDeleteView,
)

urlpatterns = [
    path("create/", ProductCreateView.as_view(), name="product_create"),
    path(
        "<slug:slug>/<uuid:pk>/", ProductDetailsView.as_view(), name="product_details"
    ),
    path(
        "<slug:slug>/<uuid:pk>/manage/",
        ProductUpdateDeleteView.as_view(),
        name="product_update_delete",
    ),
    path("", ProductsListView.as_view(), name="product_list"),
]
