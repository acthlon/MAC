from django.contrib.sites.shortcuts import get_current_site
from rest_framework import serializers
from rest_framework.reverse import reverse
from core.constants import MAX_FILE_SIZE
from core.constants import (COLOR_CHOICES, FABRIC_CARE_INSTRUCTIONS,
                            PRODUCT_SIZE_CHOICES)
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



class ProductDetailSerializer(ProductSerializer):

    similar_products = serializers.SerializerMethodField()

    def get_similar_products(self,product_obj):
        try:    
            similar_products = product_obj.get_similar_products
            serialized_similar_products = ProductSerializer(similar_products, many=True, context=self.context) 
            return serialized_similar_products.data
        
        except Exception as e:
            raise serializers.ValidationError({'error': str(e)}) 
    
    
    class Meta:
    
        model = Products
        fields = ('id','name','description','price','image','slug','discount',"get_percent_disount",'stock','quality_category','categories','similar_products') 