from rest_framework import serializers
from cart.models import Cart,CartItem
from materials.serializers import MaterialSerializer,MaterialVariantSerializer
from products.serializers import ProductSerializer
from django.db.models import Sum
from decimal import Decimal


class CartItemSerializer(serializers.ModelSerializer):

    item_type = serializers.ReadOnlyField(source='content_type.model')

    def to_representation(self, instance):

        representation = super().to_representation(instance)

        if instance.content_type.model == 'materialvariant':

            serialized_material = MaterialVariantSerializer(instance.content_object)
            representation['material_variant'] = serialized_material.data
            representation.pop('products',None) 

        elif instance.content_type.model == 'productvariant':

            serialized_product = ProductSerializer(instance.content_object)
            representation['product_variant'] = serialized_product.data
            representation.pop('materials',None)
        
        return representation

    class Meta:
        model = CartItem 
        # fields = ('id','item_type','unit_price','quantity','discount_amount','image','name','item_id')
        fields = ('id','item_type','quantity','sub_total','unit_price', 'discount_amount')


class CartSerializer(serializers.ModelSerializer):

    cartitems = CartItemSerializer(source='items',many=True,read_only=True)
    cart_items_total_price = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()
    
    def get_cart_items_total_price(self,obj):
        return obj.cart_items_total_price
    
    def get_total_discount(self,obj):
        total_discount = obj.items.aggregate(Sum('discount_amount'))['discount_amount__sum']
        
        return total_discount if total_discount else Decimal('0.00')
    
    class Meta:

        model = Cart
        fields = ('cart_code','cartitems','cart_items_total_price','total_discount')