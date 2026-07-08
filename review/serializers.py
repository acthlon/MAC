from rest_framework import serializers
from review.models  import Reviews
from materials.models import Materials
from products.models import Products
from accounts.serializers import UserProfileSerializer
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from order.models import OrderItem
from django.shortcuts import get_object_or_404
from rest_framework.reverse import reverse


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
        return obj.get_item_name 

    def get_total_customers(self,obj):
        return obj.get_total_customers
    
    def get_item_average_rating(self,obj):
        return obj.get_item_average_rating  

    def get_total_average_rating(self,obj):
        return obj.get_total_average_rating    
    
    def get_review_update_url(self,obj):
        request = self.context['request']
        # url = f'{obj.pk}/update/'
        # site_domain = get_current_site(request).domain
        # final_url = f"http://{site_domain}:8000/review/{url}"
        final_url = reverse('review_update', request=request, kwargs={'pk': obj.pk})
        
        return final_url
            

    class Meta:
        model = Reviews
        fields = ['profile','comment','rating','created_at','updated_at','item_name','item_average_rating','total_customers','total_average_rating','review_update_url','verified_purchase']


class ReviewCreateSerializer(serializers.ModelSerializer):

    def validate(self,data):

        request = self.context.get('request')
        user = request.user
        item_id = self.context.get('item_id')
        model_name = self.context.get('model_name')

        if model_name == 'materials':
            material = get_object_or_404(Materials, id=item_id)

        if model_name == 'products':
            product = get_object_or_404(Products,id=item_id)

        if model_name == 'materials':
            model_class = Materials
        elif model_name == 'products':
            model_class = Products

        content_type = ContentType.objects.get_for_model(model_class)

        has_permission = OrderItem.objects.filter(
            order__user = user,
            object_id = item_id,
            content_type = content_type,
            order__status = 'COMPLETED',order__is_active = False ).exists()

        if not has_permission:
            raise serializers.ValidationError('You can only make review for an item you have purchased and received')
        
        data['verified_purchase'] = True

        return data

    def create(self,validated_data):

        profile = self.context.get('request').user.userprofile
        item_id = self.context.get('item_id')
        model_name = self.context.get('model_name')
        slug = self.context.get('slug')

        if model_name == 'materials':

            material_id = item_id

            try:
                content_type = ContentType.objects.get_for_model(Materials)
            except Exception as e:
                raise serializers.ValidationError('Unsupported model')     
            
            review = Reviews.objects.create(**validated_data, content_type = content_type,                    object_id = material_id,
            profile = profile) 

            return review
            

        elif model_name == 'products':

            product_id = item_id

            try:

                content_type = ContentType.objects.get_for_model(Products)
            
                review = Reviews.objects.create(**validated_data,
                    profile = profile,                            
                    content_type = content_type,
                    object_id = product_id)
                
                return review
            except Exception as e:
                raise serializers.ValidationError('Product not found') 
            
        else:
            raise serializers.ValidationError('Either product_id or material_id is required') 
        
    class Meta:
        model = Reviews
        fields = ('comment','rating','verified_purchase')


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