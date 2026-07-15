from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework import status
from review.serializers import ReviewListSerializer,ReviewCreateSerializer,ReviewUpdateSerializer
from review.models import Reviews 
from rest_framework.views import APIView
from core.pagination import ReviewPagination
from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticated,AllowAny
from core.permissions import IsReviewOwnerOrReadOnly
from rest_framework import generics
from rest_framework.reverse import reverse

            
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
            
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data,status=status.HTTP_201_CREATED) 
            
        except Exception as e:
            return Response({'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)    


class ReviewListByItem(generics.ListAPIView):
    
    permission_classes = [AllowAny]
    serializer_class = ReviewListSerializer
    pagination_class = ReviewPagination
    
    def get_queryset(self):
        
        pk = self.kwargs.get('pk')
        model_name = self.kwargs.get('model_name')
        
        try:
            content_type = ContentType.objects.get(model= model_name.lower())
        except ContentType.DoesNotExist:
            raise NotFound(detail = 'Wrong model type')
        
        reviews = Reviews.objects.filter(verified_purchase=True,object_id = pk,content_type = content_type ).select_related('user').only(
            'comment',
            'rating',
            'created_at',
            'updated_at',
            'user',
            'user__profile_image',
            'user__first_name',
            'user__last_name',)

        return reviews
    
    def list(self,request,*args,**kwargs):
        response = super().list(request,*args,**kwargs)
        
        pk = self.kwargs.get('pk')
        model_name = self.kwargs.get('model_name')
        slug = self.kwargs.get('slug')
        

        link_name = 'material_details' if model_name == 'materials' else 'product_details'
        item_detail_url = reverse(link_name,request=request,kwargs = {
            'pk' : pk,
            'slug' : slug, 
        }) 
        
        response.data = {
            'item_detail_url' : item_detail_url,
            **response.data
        }
        return response



class ReviewDeleteView(generics.DestroyAPIView):

    permission_classes = [IsReviewOwnerOrReadOnly,]
    queryset = Reviews.objects.all()


class ReviewUpdateView(APIView):
    
    permission_classes = [IsReviewOwnerOrReadOnly,]
    serializer = ReviewUpdateSerializer
    queryset = Reviews.objects.all()