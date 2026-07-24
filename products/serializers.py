import datetime

from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from core.constants import FABRIC_CARE_INSTRUCTIONS, MAX_FILE_SIZE
from products.models import Products


class ProductSerializer(serializers.ModelSerializer):

    item_detail_url = serializers.SerializerMethodField()
    slug = serializers.SlugField(read_only=True)


    def get_item_detail_url(self,obj):

        request = self.context.get('request')
        url = reverse('product_details', kwargs={'slug':obj.slug, 'pk':obj.id}, request=request)
        
        return url

    def validate(self,data):
        
        request_method = self.context['request'].method

        if request_method in ['PUT','PATCH','POST']:

            if 'price' in data and data.get('price') <= 0:
                raise serializers.ValidationError('Price must be greater than 0')

            if 'discount' in data and data.get('discount') < 0: 
                raise serializers.ValidationError('Discount cannot be negative')

            if 'image' in data:
                image = data.get('image')

                if image and image.size > MAX_FILE_SIZE:
                    raise serializers.ValidationError('Image size must be less than 5MB.')  
                
            if 'stock' in data and data.get('stock') < 0:
                    raise serializers.ValidationError('stock cannot be negative')  

        return data


    def create(self,validated_data):

        request = self.context['request']
        user = request.user

        product = Products.objects.create(**validated_data, user=user)
        return product
    
    class Meta:
        
        model = Products
        fields = ('name','description','price','slug','discount',"get_percent_disount",'item_detail_url','quality_category','status','categories')     


class ProductDetailSerializer(serializers.ModelSerializer):
    
    product_info = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    grouped_variant_sizes = serializers.SerializerMethodField()
    videos = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    fabric_care = serializers.SerializerMethodField()
    reviews_data = serializers.SerializerMethodField()
    similar_products = serializers.SerializerMethodField()
    
    
    def get_product_info(self,obj):
        
        # 1. Figure out what the date was exactly 7 days ago
        seven_days_ago = timezone.now() - datetime.timedelta(days=7)
        is_new = obj.created_at >= seven_days_ago
        
        product = {
                'id': str(obj.id),
                'name': obj.name,
                'slug': obj.slug,
                'description': product.description,
                'price': float(obj.price),
                'discount': float(obj.discount) if obj.discount else None,
                'discounted_price': float(obj.discounted_price) if obj.discounted_price else None,
                'total_stock': obj.total_stock,
                'percent_discount': obj.get_percent_disount,
                'quality_category': obj.quality_category,
                'category': obj.categories.name if hasattr(obj,'categories') and obj.categories else None,
                'is_new_arrival': is_new,
                'average_rating': obj.average_rating,
                'review_count': obj.review_count,
            }
        return product
        
    
    def get_variants(self,obj):
        
        request = self.context.get('request')
        variant_list = []
        for var in obj.variants.all():
            if var.stock <= 0:
                stock_status = f'Product out of stock'
            elif var.stock <= 7:
                stock_status = f'Only {var.stock} left in stock'
            else:
                stock_status = f'In stock'
        
            variant = {   
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
                }
            
            variant_list.append(variant)
        return variant_list            
    
    
    def get_grouped_variant_sizes(self,obj):
        grouped_variant_sizes = {}
        available_colors = []
        variants = self.get_variants(obj)
        
        
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
        return grouped_variant_sizes


    def get_videos(self,obj):
        
        request = self.context.get('request')
        videos = [
            {
                "id" : vid.id,
                "video" : request.build_absolute_uri(vid.video.url) if vid.video else None,
                "thumbnail" :  request.build_absolute_uri(vid.thumbnail.url) if vid.thumbnail else None,
            } for vid in obj.videos.all()
        ]
        return videos
    
    
    def get_details(self,obj):
        spec = getattr(obj,'product_spec',None)
        specification = None 
        if not spec:
            return None
        specification = {
            
            'product_line': spec.product_line,
            'weight': float(spec.weight) if spec.weight else None,
            'material_type': spec.get_material_type_display() if spec.material_type else None,
        }
        
        details = {
            'key_features': spec.key_features,
            'specification': specification,
        }
        return details

    def get_fabric_care(self,obj):
        spec = getattr(obj,'product_spec',None)
        
        if spec and spec.material_type:
            fabric_care = FABRIC_CARE_INSTRUCTIONS.get(spec.material_type,'Dry clean only.')
            return fabric_care
        return None
       
    
    def get_reviews_data(self,obj):
        request = self.context.get('request')
        user = request.user
        pk = self.kwargs.get(pk)
        user_review = None
        
        if user and user.is_authenticated:
            user_review = user.user_reviews.filter(object_id=obj.pk,verified_purchase=True).first()
            
        reviews_qs = obj.reviews.select_related('user').all()
    
        action_urls = {
                    'review_create_url' : reverse('review_create', kwargs={
                        'model_name' : obj.model_name,'slug' : obj.slug,'pk': obj.id
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
                        'model_name' : obj.model_name,
                        'slug': obj.slug,
                        'pk' : obj.id,
                    },
                    request=request)if user_review else None
                } 
        
        reviews_list = [
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

        reviews =  {
                'action_url' : action_urls,
                'average_rating': obj.average_rating,
                'review_count': obj.review_count,
                'items': reviews_list,
            }
        return reviews
    
    def get_similar_products(self,obj):
        
        request = self.context.get('request')
        similar_products = []
                
        for pdt in obj.get_similar_products:
            
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
        return similar_products

         
    
    class Meta:
        fields = ('product_info','variants','grouped_variant_sizes','videos','details','fabric_care','reviews_data','similar_products',)