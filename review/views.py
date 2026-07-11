from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from review.serializers import ReviewSerializer,ReviewCreateSerializer,ReviewSerializerUpdate
from review.models import Reviews 
from rest_framework.views import APIView
from materials.models import Materials
from products.models import Products
from core.pagination import ReviewPagination
from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticated,AllowAny
from core.permissions import IsReviewOwnerOrReadOnly,IsAdminOrReadOnly
from rest_framework import generics


class ReviewListView(generics.ListAPIView):

    permission_classes = [AllowAny,]
    perginator_class = ReviewPagination
    serializer_class = ReviewSerializer

    # without generics apiview you will use this get function belowi
    # def get(self,request):
    #     try:
    #         reviews = Reviews.objects.select_related('user').filter(verified_purchase=True ).order_by('?')[:6]
    #     except Reviews.DoesNotExist:
    #         return Response({'message':'Reviews Not Found'})
        
    #     serializer = ReviewSerializer(reviews,many=True, context = {'request': request})
    #     return Response(serializer.data)

    def get_queryset(self):

        user = self.request.user

        if not user.is_staff:
            queryset = Reviews.objects.select_related('user').filter(verified_purchase = True).order_by('?')[:6]

            return queryset
        
        elif user.is_staff:
            queryset = Reviews.objects.all()

            return queryset

            
class ReviewCreateView(APIView):

    permission_classes = [IsAuthenticated,]

    def post(self,request,pk,model_name,slug):
        
        try:
            serializer = ReviewCreateSerializer(data = request.data, context={
                'request':request,
                'item_id':pk,
                'model_name':model_name.lower(),
                'slug':slug
            })    
            
            if serializer.is_valid():
                serializer.save()

                return Response(serializer.data,status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)  
            
        except Exception as e:
            # NOTE: STOP RETURNING THINGS LIKE `{'message':str(e)}`, just say {'message':"Error occurred try again"},
            # You should only log the exact error `str(e)`, don't return them.
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)    
        

class ReviewListByItem(APIView):

# use generic apiview here

    permission_classes = [AllowAny,]

    def get(self,request,pk,model_name,slug):

        try: 
            content_type = ContentType.objects.get(model = model_name)
        except ContentType.DoesNotExist:
            return Response({'error': 'Wrong model type'},status=status.HTTP_400_BAD_REQUEST)

        review = Reviews.objects.filter(content_type=content_type, object_id=pk, verified_purchase = 'True').select_related('user').order_by('-created_at')
        
        paginator = ReviewPagination()
        paginated_review = paginator.paginate_queryset(review,request)

        serializer = ReviewSerializer(paginated_review, context = {'request': request}, many=True)

        return paginator.get_paginated_response(serializer.data)


class ReviewDeleteView(APIView):

    permission_classes = [IsReviewOwnerOrReadOnly,]

    def delete(self,request,pk):
        try:
            review =Reviews.objects.get(id=pk)
            self.check_object_permissions(self.request,review)    # this line here triggers object level permission
        except Reviews.DoesNotExist: 
            return Response({'message':'review not found'})  

        review.delete()
        return Response({'message':'Review deleted successfully'},status=status.HTTP_204_NO_CONTENT)   


class ReviewUpdateView(APIView):
    
    permission_classes = [IsReviewOwnerOrReadOnly,]

    def put(self,request,pk):

        try:
            review = Reviews.objects.get(pk=pk)
            self.check_object_permissions(self.request,review)
        except Reviews.DoesNotExist:
            return Response({'message':'review not found'})  
            
        serializer = ReviewSerializerUpdate(review,data=request.data,partial=True,context = {'request':request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)