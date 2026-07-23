from django.shortcuts import render
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from core.constants import (COLOR_CHOICES, FABRIC_CARE_INSTRUCTIONS,
                            PRODUCT_SIZE_CHOICES)
from core.pagination import CatalogPagination
from core.permissions import IsAdminOrReadOnly
from products.filters import ProductFilter
from products.models import Products
from products.serializers import ProductSerializer
from django.shortcuts import get_object_or_404



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


class ProductDetailView(APIView):

    permission_classes = [AllowAny]

    def get(self,request,slug,pk):
        
        user = request.user
        
        try:
            product = Products.objects.prefetch_related(
                'variant',
                'videos',
                'reviews'
            ).select_related(
                'product_spec',
                'categories').get(slug=slug,id=pk)
        
        except Exception as e:
            return Response({'message':str(e)})
        
        new_arrivals = Products.objects.filter(is_active=True).order_by('-created_at')[:8]
        
        spec = getattr(product,'product_spec',None)
        categories = getattr(product,'categories',None)
        
        
        # STOCK STATUS
        for variant in product.variant.all():
            if variant.stock <= 0:
                stock_status = f'Product out of stock'
            elif variant.stock <= 7:
                stock_status = f'Only {variant.stock} left in stock'
            else:
                stock_status = f'In stock'
        
        
        variants = [
                {   
                    'id' : var.id,
                    'size_code' : var.size,
                    'size': var.get_size_display() if var.size else None,
                    'stock' : var.stock,
                    'stock_status': stock_status,
                    'sku' : var.sku,
                    'color_code' : var.color,
                    'color': var.get_color_display() if var.color else None,
                    'price': float(var.final_price) if var.final_price else None,
                    'images' : 
                        [
                            {
                                "id" : img.id,
                                "image" : request.build_absolute_uri(img.image.url) if img.image else None,
                                "is_pry" : img.is_primary,
                                "display_order" : img.display_order
                            } for img in var.images.all()
                        ]
                } for var in product.variant.all()
            ]


        grouped_variant_sizes = {}
        available_colors = []

        for variant in variants:
            color_key = variant.get('color')
            
            if color_key not in available_colors:
                available_colors.append(color_key)
            
            
            if color_key not in grouped_variant_sizes:
                grouped_variant_sizes[color_key] = []
                
            grouped_variant_sizes[color_key].append({
                            'size_code': variant.get('size_code'),
                            'size': variant.get('size'),
                            'stock': variant.get('stock'),
                            })


        videos = [
            {
                "id" : vid.id,
                "video" : request.build_absolute_uri(vid.video.url) if vid.video else None,
                "thumbnail" :  request.build_absolute_uri(vid.thumbnail.url) if vid.thumbnail else None,
            } for vid in product.videos.all()
        ]

        
        specification = None 
        if spec:
            
            specification = {
                
                'product_line': spec.product_line,
                'weight': float(spec.weight) if spec.weight else None,
                'material_type': spec.get_material_type_display() if spec.material_type else None,
            }
            
        
        fabric_care = None
        if spec and spec.material_type:
            fabric_care = FABRIC_CARE_INSTRUCTIONS.get(spec.material_type,'Dry clean only.')

        if user.is_authenticated:
            
            user_review = user.user_reviews.filter(object_id=pk,verified_purchase=True).first()

                
        reviews_qs = product.reviews.select_related('user').all()
    
        action_urls = {
                    'review_create_url' : reverse('review_create', kwargs={
                        'model_name' : product.model_name,'slug' : product.slug,'pk': product.id
                        },
                        request=request),
                    
                    'review_update_url' : reverse('review_update',kwargs= {
                        'pk': user_review.id  
                    },
                     request=request) if user_review else None,
                    
                    'review_delete_url' : reverse('review_delete', kwargs={
                        'pk' : user_review.id
                    },
                     request=request) if user_review else None,
                    
                    'all_reviews' : reverse('all_single_item_review', kwargs={
                        'model_name' : product.model_name,
                        'slug': product.slug,
                        'pk' : product.id,
                    },
                    request=request)if user_review else None
                } 
        
        reviews_data = [action_urls] + [
            {
                'id' : review.id,
                'username' : review.user.username,
                'comment' : review.comment,
                'verified_purchase' : review.verified_purchase,
                'rating'  : review.rating,
                'rating_display' : review.get_rating_display(),
                'date' : review.created_at.strftime('%B %d, %Y'),
                
            } for review in reviews_qs
        ] 



        similar_products = []
                
        for pdt in product.get_similar_products:
            
            first_variant = pdt.variant.first()
            first_image_obj = first_variant.images.filter(is_primary=True).first() if first_variant else None
            
            similar_products.append({
                'id' : pdt.id,
                'name' : pdt.name,
                'price' : float(pdt.price),   # we are using float because the price is stored as decimal in the D.B and json doesn't understand decimal so it will convert the value to string,
                'image': request.build_absolute_uri(first_image_obj.image.url) if first_image_obj and first_image_obj.image else None,
                'avg_rating' : pdt.average_rating,
                'review_count' : pdt.review_count, 
                'link': reverse('product_details', request=request, kwargs={'slug': pdt.slug, 'pk': pdt.id}),
            })
        
        
    
        # FINAL RESPONSE

        data = {
            'product': {
                'id': str(product.id),
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'discount': float(product.discount) if product.discount else None,
                'discounted_price': float(product.discounted_price) if product.discounted_price else None,
                'total_stock': product.total_stock,
                'percent_discount': product.get_percent_disount,
                'quality_category': product.quality_category,
                'category': product.categories.name if product.categories else None,
                'is_new_arrival': True if product in new_arrivals else False,
                'average_rating': product.average_rating,
                'review_count': product.review_count,
            },

            'variants': variants,
            'grouped_variant_sizes': grouped_variant_sizes,
            'videos': videos,
        
            'description': product.description,
                            
            'details': {
                'key_features': spec.key_features if spec else None,
                'specification': specification,
            },
            
            'fabric_care': fabric_care,
            # 'shipping_returns': 'Free shipping on orders over ₦50,000. Easy returns within 7 days.',

            'reviews': {
                'average_rating': product.average_rating,
                'review_count': product.review_count,
                'items': reviews_data,
            },

            'similar_products': similar_products,
        }

        return Response(data, status=status.HTTP_200_OK)