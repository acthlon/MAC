from django.shortcuts import render
from materials.models import Materials
from rest_framework.response import Response
from materials.models import Materials
from materials.serializers import MaterialSerializer
from rest_framework import status
from rest_framework.views import APIView 
from  materials.filters import MaterialsFilter


class MaterialsView(APIView):
    
    def get(self,request):
        
        try:

            filterset = MaterialsFilter(request.query_paraams, Materials.objects.all())

            if filterset.is_valid():
                materials = filterset.qs
                serializer = MaterialSerializer(materials,many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            return Response(filterset.errors,status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({'message': str(e)},status=status.HTTP_400_BAD_REQUEST)
            
            
class MaterialCreateView(APIView):    

    def post(self,request):
        serializer = MaterialSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        
        return Response(serializer.error,status=status.HTTP_400_BAD_REQUEST)

class MaterialDetailsView(APIView):
    
    def get(self,request,pk):

        try:
            material = Materials.objects.get(pk=pk)

        except Materials.DoesNotExist:
            return Response({'message':'material not found'},status=status.HTTP_400_BAD_REQUEST)
        
        serializer = MaterialSerializer(material)
        return Response(serializer.data)


class MaterialUpdateView(APIView):


    def put(self,request,pk):
        try:
            material = Materials.objects.get(pk=pk)

        except Materials.DoesNotExist():
            return Response({'message':'material does not exist'},status=status.HTTP_400_BAD_REQUEST)    
    
        serializer = MaterialSerializer(material, data = request.data)

        if serializer.is_valid:
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.error,status=status.HTTP_400_BAD_REQUEST)


class MaterialDeleteView(APIView):


    def delete(self,request,pk):
        try:
            material = Materials.objects.get(pk=pk)
        except Materials.DoesNotExist():
            return Response({'message':'material not found'})

        material.delete()
        return Response({'message':'material deleted successfully'},status=status.HTTP_204_NO_CONTENT)         
    
