from rest_framework import serializers
from order.models import Address ,Order,OrderItem,PaymentMethod,DeliveryMethod,PAYMENT_METHOD_CHOICES
from django.shortcuts import get_object_or_404

class AddressSerializer(serializers.ModelSerializer):

    def create(self,validated_data):

        address = Address.objects.create(**validated_data)
        address.save()
        return address
    
    def update(self,instance,validated_data):

        for fields,value in validated_data.items():
            if hasattr(instance,fields):
                setattr(instance,fields,value)
                instance.save()
        return instance        


    class Meta:
        model = Address
        fields = [
            'first_name','last_name','phone_number','delivery_address','city','state','country','address_type','is_default','additional_info','created_at','updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrderItemSerialzer(serializers.ModelSerializer):

    item_image = serializers.SerializerMethodField()
    item_type = serializers.CharField(source='content_type.model')
    item_name = serializers.CharField(source='content_type.name')
    item_slug = serializers.CharField(source='content_type.slug')

    def get_item_image(self,obj):

        image = getattr(obj.content_object, 'image', None)
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_url(image.url)
            return image.url
        return None

    
    class Meta:
        model = OrderItem
        field = ['id','item_image','item_type','item_name','item_slug','quantity','unit_price','sub_total','discount_amount']



class OrderListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order 
        fields = ['id', 'status', 'delivery_status', 'total_amount', 'total_items', 'created_at']

class OrderDetailSerializer(serializers.ModelSerializer):

    orderitems = OrderItemSerialzer(many=True, read_only=True)
    shipping_address = serializers.SerializerMethodField(read_only=True)

    class Meta:

        model = Order
        fields = ['id','shipping_address','total_amount','total_items','delivery_fee','status','created_at','updated_at','delivery_status' 'payment_method', 'payment_reference']

        def get_shipping_address(self,obj):
            request = self.context['request']

            shipping_address = obj.shipping_address
            serializer = AddressSerializer(shipping_address,  many=True, context={'request' : request})
            return serializer.data



class PaymentMethodSerializer(serializers.ModelSerializer):

    value = serializers.CharField(source='code')
    icon_url = serializers.SerializerMethodField()

    def get_icon_url(self,obj):
        return obj.icon_url
    

    def to_representation(self,instance):

        representation = super().to_representation(instance)
        representation['is_selected'] = False
        return representation
    
    class Meta:
        model = PaymentMethod
        fields = ['id','value','display_name','description','icon_url','is_pre_pay','requires_registration']



class DeliveryMethodSerializer(serializers.ModelSerializer):

    def to_representation(self,instance):

        representation = super().to_representation(instance)
        representation['is_selected'] = False
        return representation
    
    class Meta:
        models = DeliveryMethod
        fields = ['id','user','name','description','cost','delivery_time']


class CreateOrderFromCartSerializer(serializers.ModelSerializer):

    shipping_address_id = serializers.UUIDField(required = True)
    billing_address_id = serializers.UUIDField(required=False,allow_null=True)
    use_shipping_as_billing = serializers.BooleanField(default=True,required=False)
    payment_method = serializers.ChoiceField(choices = PAYMENT_METHOD_CHOICES, required=True)

    def validate_shipping_address_id(self,value):
        
        user = self.context['request'].user
        address = get_object_or_404(Address, user=user, id=value)
        return address
    
    def validate_billing_address_id(self,value):

        user = self.context['request']
        address = get_object_or_404(Address, user=user, id=value)
        return address

    def validate(self,data):

        shipping_as_billing = data.get('use_billing_as_shipping')
        shipping_address_id = data.get('shipping_address_id')
        billing_address_id = data.get('billing_address_id')

        if shipping_as_billing:
            data['billing_address_id'] = shipping_address_id
        else:
            if not billing_address_id:
                raise serializers.ValidationError('Billing address required when not using shipping address')   

            data['billing_address_id'] = billing_address_id

        return data    
            

        


    

# PROCESSES OF USING GIT AND GITHUB

# install git

# # conigure username and e-mail

# git config --global user.name " your username"
# git config --global user.email "your email"

# # initialize your git

# git init

# # add your file or folder to staging area and commit your changes
# git add filename or . (for the whole folder)
# git commit -m "commit message on changes you have made"

# # to push to github, you have to connect the local repo to the remote repo
 
# git remote add origin " url of remote repo "

# # to very the connection, This will show the new nickname and the URL associated with it.
# git remote -v (v - means verbose)

# # you can now push or pull

# git push origin master/main
# git pull origin master/main

# to create a short cut insgtead of writing the full command to pull or push, you can just run this comand 

# git push -set-upstream origin master/main