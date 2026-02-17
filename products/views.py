from django.shortcuts import render
from rest_framework.views import APIView
from products.serializers import ProductSerializer,ProductDetailSerializer
from products.filters import ProductFilter
from products.models import Products
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny 
from rest_framework import status
from core.pagination import CatalogPagination
from rest_framework import generics
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.filters import SearchFilter,OrderingFilter
from core.permissions import IsAdminOrReadOnly



class ProductsListView(generics.ListAPIView):
    
    
    permission_classes = [AllowAny,]

    def get_queryset(self):

        if self.request.user.is_staff:
            queryset = Products.objects.all()
            return queryset
        
        elif not self.request.user.is_staff:
            queryset = Products.objects.filter(is_active = True)
            return queryset

    paginator_class = CatalogPagination
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_class = ProductFilter
    search_fields = ['name','description']
    ordering_fields = ['price','category']

        

           
class ProductDetailView(APIView):


    permission_classes = [AllowAny,]
    
    def get(self,request,pk,slug):

        try:
            product = Products.objects.get(pk=pk,slug=slug)
        except Products.DoesNotExist:
            return Response('Product does not exist')
            
        serializer = ProductDetailSerializer(product, context = {'request':request})
        return Response(serializer.data)
    

class ProductCreateView(APIView):

    permission_classes = [IsAdminOrReadOnly]

    def post(self,request):

        serializer = ProductSerializer(data= request.data, context = {'request':request})

        try:
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.data,status=status.HTTP_201_CREATED) 
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)     



class ProductDeleteView(APIView):

    permission_classes = [IsAdminOrReadOnly]

    def delete(self,request,pk,slug):

        try:

            product = Products.objects.get(pk=pk,slug=slug)
        except Products.DoesNotExist:
            return Response({'message':'Product does not exist'})  

        product.delete()
        return Response({'message':'Product deleted successfully'}, status=status.HTTP_204_NO_CONTENT)  



class ProductUpdateView(APIView):

    permission_classes = [IsAdminOrReadOnly]

    def put(self,request,pk,slug):

        try:                                    
           product = Products.objects.get(pk=pk,slug=slug)
        except Products.DoesNotExist:
            return Response('Product not found')  
        
        serializer = ProductSerializer(product, data=request.data, context = {'request': request},partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)