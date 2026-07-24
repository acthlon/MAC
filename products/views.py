from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from core.pagination import CatalogPagination
from core.permissions import IsAdminOrReadOnly
from products.filters import ProductFilter
from products.models import Products
from products.serializers import ProductDetailSerializer, ProductSerializer


class ProductsListView(generics.ListAPIView):
    
    
    permission_classes = [AllowAny,]

    def get_queryset(self):

        if self.request.user.is_staff:
            queryset = Products.objects.all()
            return queryset
        
        elif not self.request.user.is_staff:
            queryset = Products.objects.filter(status = True)
            return queryset

    paginator_class = CatalogPagination
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class = ProductFilter
    search_fields = ['name','description']
    ordering_fields = ['price','quality_category']

    

class ProductCreateView(generics.CreateAPIView):

    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductSerializer
    
    def get_serializer_context(self):
        
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ProductDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAdminOrReadOnly]
    queryset = Products.objects.all()

    def get_object(self):
        
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')
        
        product = get_object_or_404(queryset,pk=pk,slug=slug)
        return product


class ProductUpdateView(generics.UpdateAPIView):

    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ProductSerializer
    queryset = Products.objects.all()

    def get_object(self):
        
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')

        product = get_object_or_404(queryset,pk=pk,slug=slug)
        return product



class ProductDetailsView(generics.RetrieveAPIView):
    
    permission_classes = [AllowAny,]
    serializer_class = ProductDetailSerializer
    
    def get_queryset(self):
        products = Products.objects.prefetch_related(
            'variant',
            'videos',
            'reviews'
        ).select_related(
            'product_spec',
            'categories')
        return products

    def get_object(self):
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')
        
        product = get_object_or_404(queryset,pk=pk,slug=slug)
        return product