from rest_framework import serializers
from products.models import Products
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.reverse import reverse

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

            if 'name' in data:
                name = data.get('name').strip()

                if name.replace('?','').isalpha():
                    raise serializers.ValidationError(f'Name should contain only alphabet')

            if 'description' in data:
                description = data.get('description').strip()

                if description.replace('?','').isalpha():
                    raise serializers.ValidationError(f'description should contain only alphabet {print(description)}')

            if 'price' in data:
                price = data.get('price')

                if price <= 0:
                    raise serializers.ValidationError('Price must be greater than 0')


            if 'discount' in data:
                discount = data.get('discount')

                if not discount <= 0:
                    raise serializers.ValidationError('Discount must be greater than 0')

            if 'image' in data:
                image = data.get('image')

                if image and image.size > 5 * 1024 * 1024:
                    raise serializers.ValidationError('Image size must be less than 5MB.')  
                
            if 'stock' in data:
                stock = data.get('stock')
                if not stock >= 1:
                    raise serializers.ValidationError('stock must be greater than zero')  

        return data


    def update(self,instance,validated_data):
        
        for field,value in validated_data.items():
            if hasattr(instance,field):
                setattr(instance,field,value)
                instance.save()

        return instance         
    

    def create(self,validated_data):

        request = self.context['request']
        user = request.user

        product = Products.objects.create(**validated_data, user=user)
        product.save()
        return product
    

    def update(self,instance,validated_data):
        
        for field,value in validated_data.items():
            if hasattr(instance,field):
                setattr(instance,field,value)
        
        instance.save()
        return instance    


    class Meta:
        
        model = Products
        fields = ('name','description','price','image','slug','discount',"get_percent_disount",'stock','item_detail_url','quality_category','is_active','categories')     



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