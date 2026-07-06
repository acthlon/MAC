from django.urls import path
from products.views import ProductsListView,ProductDetailView,ProductCreateView,ProductDeleteView,ProductUpdateView


urlpatterns = [
    path('list/',ProductsListView.as_view(),name = 'product_list'),
    path('<slug:slug>/<uuid:pk>/',ProductDetailView.as_view(),name='product_details'),
    path('create/',ProductCreateView.as_view(),name='product_create'),
    path('<slug:slug>/<uuid:pk>/delete/',ProductDeleteView.as_view(),name='product_delete'),
    path('<slug:slug>/<uuid:pk>/update/',ProductUpdateView.as_view(),name='product_update'),
    ]
