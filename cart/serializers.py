from rest_framework import serializers
from cart.models import Cart,CartItem
from materials.serializers import MaterialSerializer
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):

    item_type = serializers.ReadOnlyField(source='content_type.model')

    def to_representation(self, instance):

        representation = super().to_representation(instance)

        if instance.content_type.model == 'materials':

            serialized_material = MaterialSerializer(instance.content_object)
            representation['material'] = serialized_material.data
            representation.pop('products',None) 

        elif instance.content_type.model == 'products':

            serialized_product = ProductSerializer(instance.content_object)
            representation['product'] = serialized_product.data
            representation.pop('materials',None)
        
        return representation

    class Meta:
        model = CartItem 
        # fields = ('id','item_type','unit_price','quantity','discount_amount','image','name','item_id')
        fields = ('id','item_type','quantity','sub_total')


class CartSerializer(serializers.ModelSerializer):

    cartitems = CartItemSerializer(source='items',many=True,read_only=True)
    cart_total = serializers.SerializerMethodField()

    def get_cart_total(self,obj):
        return obj.cart_total()
        
    class Meta:

        model = Cart
        fields = ('cart_code','cartitems','cart_total')