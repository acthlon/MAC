from django.shortcuts import render
from rest_framework import generics
from materials.models import Materials
from rest_framework.response import Response
from materials.models import Materials
from materials.serializers import MaterialSerializer,MaterialDetailSerializer
from rest_framework import status
from rest_framework.views import APIView 
from  materials.filters import MaterialsFilter
from rest_framework.permissions import IsAuthenticated,AllowAny 
from core.pagination import CatalogPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter,OrderingFilter
from core.permissions import IsAdminOrReadOnly 




class MaterialsListView(generics.ListAPIView):
    
    permission_classes = [AllowAny,]

    def get_queryset(self):

        user = self.request.user

        if user.is_staff:
            queryset =  Materials.objects.all()     
            return queryset
        
        elif not user.is_staff:
            queryset =  Materials.objects.filter(is_active=True)
            return queryset
        
    serializer_class = MaterialSerializer 
    paginator_class = CatalogPagination 

    filter_backends = (DjangoFilterBackend,SearchFilter,OrderingFilter)

    filterset_class = MaterialsFilter    
    search_fields = ('name','description')
    ordering_fields = ('price','category')
            
            
class MaterialCreateView(APIView):    


    permission_classes = [IsAdminOrReadOnly,]

    def post(self,request):

        try:
            serializer = MaterialSerializer(data=request.data,context={'request':request})
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            else:
                
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        
class MaterialDetailsView(APIView):
    
    permission_classes = [AllowAny,]

    def get(self,request,pk,slug):

        try:
            material = Materials.objects.get(pk=pk,slug=slug)

        except Materials.DoesNotExist:
            return Response({'message':'material not found'},status=status.HTTP_400_BAD_REQUEST)
        
        serializer = MaterialDetailSerializer(material)
        return Response(serializer.data)


class MaterialUpdateView(APIView):


    permission_classes = [IsAdminOrReadOnly,]

    def patch(self,request,pk,slug):
        try:
            material = Materials.objects.get(pk=pk,slug=slug)

        except Materials.DoesNotExist():
            return Response({'message':'material does not exist'},status=status.HTTP_400_BAD_REQUEST)    
    
        serializer = MaterialSerializer(material, data = request.data, context = {'request': request},partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class MaterialDeleteView(APIView):

    permission_classes = [IsAdminOrReadOnly,]
    
    def delete(self,request,pk,slug):
        try:
            material = Materials.objects.get(pk=pk,slug=slug)
        except Materials.DoesNotExist:
            return Response({'message':'material not found'})

        material.delete()
        return Response({'message':'material deleted successfully'},status=status.HTTP_204_NO_CONTENT)         
    
