from rest_framework import serializers
from review.models  import Reviews
from materials.models import Materials
from products.models import Products
from accounts.serializers import UserProfileSerializer
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site



class ReviewSerializer(serializers.ModelSerializer):

    profile = UserProfileSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    item_name = serializers.SerializerMethodField(read_only=True)
    total_customers = serializers.SerializerMethodField(read_only=True,required = False)
    item_average_rating = serializers.SerializerMethodField(read_only=True,required = False)
    total_average_rating = serializers.SerializerMethodField(read_only=True,required = False)
    verified_purchase = serializers.BooleanField(read_only=True,required = False)
    review_update_url = serializers.SerializerMethodField()


    def get_item_name(self,obj) :
        return obj.get_item_name()   

    def get_total_customers(self,obj):
        return obj.get_total_customers()
    
    def get_item_average_rating(self,obj):
        return obj.get_item_average_rating()  

    def get_total_average_rating(self,obj):
        return obj.get_total_average_rating()    
    
    def get_review_update_url(self,obj):
        request = self.context['request']
        url = f'{obj.pk}/update/'
        site_domain = get_current_site(request).domain
        final_url = f"http://{site_domain}:8000/review/{url}"
        return final_url
            

    class Meta:
        model = Reviews
        fields = ['profile','comment','rating','created_at','updated_at','item_name','item_average_rating','total_customers','total_average_rating','review_update_url','verified_purchase']


class ReviewCreateSerializer(serializers.ModelSerializer):

    def create(self,validated_data):

        object = self.instance
        profile = self.context.get('request').user.userprofile
        item_id = self.context.get('item_id')
        model_name = self.context.get('model_name')
        slug = self.context.get('slug')

        if model_name == 'materials':

            material_id = item_id

            try:
                material = Materials.objects.get(id=material_id,slug=slug)
                content_type = ContentType.objects.get_for_model(Materials)

                if object.profile.user.order.status != 'COMPLETED': 

                    raise serializers.ValidationError('You can only make review for an item you have bought')
                else:
                    review = Reviews.objects.create(**validated_data, content_type = content_type,
                    object_id = material.id,
                    profile = profile) 

                    return review
            
            except Exception as e:
                raise serializers.ValidationError('Material not found') 

        elif model_name == 'products':

            product_id = item_id

            try:
                product = Products.objects.get(id=product_id,slug=slug)
                content_type = ContentType.objects.get_for_model(Products)
            
                review = Reviews.objects.create(**validated_data,
                    profile = profile,                            
                    content_type = content_type,
                    object_id = product.id)
                
                return review
            except Exception as e:
                raise serializers.ValidationError('Product not found') 
            
        else:
            raise serializers.ValidationError('Either product_id or material_id is required') 
        
    class Meta:
        model = Reviews
        fields = ('comment','rating')


class ReviewSerializerUpdate(serializers.ModelSerializer):


    def update(self,instance,validated_data):

        for field,value in validated_data.items():
            if hasattr(instance,field):
                setattr(instance,field,value)    
        
        instance.save()
        return instance    
    
    class Meta:
        model = Reviews
        fields = ('comment','rating','verified_purchase')