from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.reverse import reverse
from review.models import Reviews
from materials.models import Materials
from products.models import Products
from .models import Banner, Category


class HomePageAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        banners = Banner.objects.filter(is_active=True).order_by('display_order')
        categories = Category.objects.filter(is_active=True).select_related('target_model').order_by('display_order')
        featured_products = Products.objects.filter(is_active=True, discount__gt = 15000).order_by('-created_at')[:8]
        new_arrivals = Products.objects.filter(is_active=True).order_by('-created_at')[:8]
        reviews = Reviews.objects.filter(verified_purchase=True).select_related('user').only(
            'comment',
            'rating',
            'user',
            'user__profile_image',
            'user__first_name',
            'user__last_name',
        )[:8]

        # Dynamically generate correct URLs
        product_list_url = reverse('product_list', request=request)
        material_list_url = reverse('material_list', request=request)


        # Separate categories based on their target model
        product_categories = [c for c in categories if c.target_model and c.target_model.model == 'products']
        
        material_categories = [c for c in categories if c.target_model and c.target_model.model == 'materials']
        
        

        data = {
            
            'average_rating' : Reviews.get_total_average_rating(),
            'total_customers' : Reviews.get_total_customers(),
            'satisfaction_rate' : Reviews.satisfacton_rate(),
            
            'hero_actions' :
                {
                    "button_text_dresses": "Shop Dresses",
                    "button_link_products": product_list_url,
                    "button_text_fabrics": "Shop Fabrics",
                    "button_link_fabrics": material_list_url
                },
                
            "banners": [
                {
                    "id": b.id,
                    "title": b.title,
                    "subtitle": b.subtitle,
                    "image": request.build_absolute_uri(b.image.url) if b.image else None,
                } for b in banners
            ],

            "product_categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "image": request.build_absolute_uri(cat.image.url) if cat.image else None,
                    "icon": request.build_absolute_uri(cat.icon.url) if cat.icon else None,
                    "link": f"{product_list_url}?categories={cat.name}" if cat.name else "#"
                } for cat in product_categories
            ],

            "material_categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "image": request.build_absolute_uri(cat.image.url) if cat.image else None,
                    "icon": request.build_absolute_uri(cat.icon.url) if cat.icon else None,
                    "link": f"{material_list_url}?categories={cat.name}" if cat.name else "#"
                } for cat in material_categories
            ],

            "featured_products": [
                {
                    "id": item.id,
                    "name": item.name,
                    "price": float(item.price),
                    "image": request.build_absolute_uri(item.variant.filter(is_ative=True).first().images.first().image.url) if getattr(item, 'image', None) else None,
                    "slug": getattr(item, 'slug', ''),
                    "disount" : item.discount,
                    "reviews" : item.average_rating,
                    "no_of reviews" : item.review_count,
                    "percent_discount" : item.get_percent_disount,
                    "link": reverse('product_details',request=request,kwargs={'slug':item.slug,'pk':item.id}) 
                } for item in featured_products
            ],

            "new_arrivals": [
                {
                    "id": item.id,
                    "name": item.name,
                    "price": float(item.price),
                    "image": request.build_absolute_uri(item.image.url) if getattr(item, 'image', None) else None,
                    "slug": getattr(item, 'slug', ''),
                    "link": reverse('product_details',request=request,kwargs={'slug':item.slug,'pk':item.id}) 
                } for item in new_arrivals
            ],
            
            "reviews" : [
                {
                    'comment' : review.comment,
                    'rating' : review.rating,
                    'profile_image' : request.build_absolute_uri(review.user.profile_image.url) if review.user.profile_image else None,
                    'first_name' : f'{review.user.first_name.capitalize()}' if getattr(review.user,'first_name',None) else None,
                    'last_name' : f'{review.user.last_name[0].upper()}' if getattr(review.user, 'last_name', None) else None,
                    'date' : review.created_at.strftime('%B %d, %Y')
                } for review in reviews
            ]
        }

        return Response(data)