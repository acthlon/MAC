from django.contrib.sites.shortcuts import get_current_site
from rest_framework import serializers
from rest_framework.reverse import reverse

from materials.models import Materials, MaterialVariant


class MaterialSerializer(serializers.ModelSerializer):


    item_detail_url = serializers.SerializerMethodField()
    slug = serializers.SlugField(read_only=True)


    def get_item_detail_url(self,obj):

        request = self.context.get('request')
        url = reverse('material_details',kwargs={'slug':obj.slug, 'pk':obj.id},request=request)
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

                if discount <= 0:
                    raise serializers.ValidationError('Discount must be greater than 0')

            if 'image' in data:
                image = data.get('image')

                if image and image.size > 5 * 1024 * 1024:
                    raise serializers.ValidationError('Image size must be less than 5MB.')  
        return data


    def create(self,validated_data):

        request = self.context.get('request')
        user = request.user

        material = Materials.objects.create(**validated_data,user=user)
        material.save()             
        return material



    def update(self,instance,validated_data):
        
        for field,value in validated_data.items():
            if hasattr(instance,field):
                setattr(instance,field,value)
        
        instance.save()
        return instance     

    class Meta:
        model = Materials
        fields = ('id','name','description','price','quality_category','slug','discount',"get_percent_disount",'item_detail_url','is_active',"categories",)



class MaterialDetailSerializer(serializers.ModelSerializer):


    similar_material = serializers.SerializerMethodField()

    def get_similar_material(self,material_obj):

        try:
            similar_material = material_obj.get_similar_material
            serialized_similar_material = MaterialSerializer(similar_material, many=True, context=self.context)
            return serialized_similar_material.data
        
        except Exception as e:
            raise serializers.ValidationError({'error': str(e)}) 

    class Meta:
        model = Materials
        fields = ('id','name','description','price','image','quality_category','color','slug','stock','discount',"get_percent_disount",'similar_material',"categories",)        
        
        
        
class MaterialVariantSerializer(serializers.ModelSerializer):
    
    
    class Meta:
        model = MaterialVariant
        fields = ('stock','sku','color','price_adjustment',)