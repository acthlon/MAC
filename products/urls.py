from django.urls import path
from products.views import ProductsListView,ProductDetailView,ProductCreateView,ProductDeleteView,ProductUpdateView


urlpatterns = [
    path('list/',ProductsListView.as_view(),name = 'product-list'),
    path('<slug:slug>/<uuid:pk>/',ProductDetailView.as_view(),name='product-details'),
    path('create/',ProductCreateView.as_view(),name='product-create'),
    path('<slug:slug>/<uuid:pk>/delete/',ProductDeleteView.as_view(),name='product-delete'),
    path('<slug:slug>/<uuid:pk>/update/',ProductUpdateView.as_view(),name='product-update'),
    ]
