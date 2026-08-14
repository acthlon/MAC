from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from rest_framework import serializers

from cart.models import Cart, CartItem
from materials.models import MaterialVariant
from products.models import ProductVariant
from products.serializers import ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    item_type = serializers.ReadOnlyField(source="content_type.model")

    class Meta:
        model = CartItem
        # fields = ('id','item_type','unit_price','quantity','discount_amount','image','name','item_id')
        fields = (
            "id",
            "item_type",
            "quantity",
            "sub_total",
            "unit_price",
            "discount_amount",
        )

    def to_representation(self, instance):

        representation = super().to_representation(instance)

        if instance.content_type.model == "materialvariant":
            serialized_material = MaterialVariantSerializer(instance.content_object)
            representation["material_variant"] = serialized_material.data
            representation.pop("products", None)

        elif instance.content_type.model == "productvariant":
            serialized_product = ProductSerializer(instance.content_object)
            representation["product_variant"] = serialized_product.data
            representation.pop("materials", None)

        return representation


class CartSerializer(serializers.ModelSerializer):
    cartitems = CartItemSerializer(source="items", many=True, read_only=True)
    cart_items_total_price = serializers.SerializerMethodField()
    total_discount = serializers.SerializerMethodField()

    def get_cart_items_total_price(self, obj):
        return obj.cart_items_total_price

    def get_total_discount(self, obj):
        total_discount = obj.items.aggregate(Sum("discount_amount"))[
            "discount_amount__sum"
        ]

        return total_discount if total_discount else Decimal("0.00")

    class Meta:
        model = Cart
        fields = ("cart_code", "cartitems", "cart_items_total_price", "total_discount")


class AddToCartSeralizer(serializers.Serializer):
    material_var_id = serializers.UUIDField(required=False, allow_null=True)
    product_var_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1)

    def validate(self, data):

        material_var_id = data.get("material_variant_id")
        product_var_id = data.get("product_variant_id")

        if not (material_var_id or product_var_id):
            raise serializers.ValidationError(
                {"message": "Either material_var_id or product_var_id is required"}
            )

        if material_var_id and product_var_id:
            raise serializers.ValidationError(
                {"message": "Send only one: material_var_id or product_var_id"}
            )

        if product_var_id:
            try:
                item = ProductVariant.objects.get(id=product_var_id)
                data["item_variant"] = item
                data["is_product"] = True
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError(
                    {"message": "Product Variant not found"}
                )

        elif material_var_id:
            try:
                item = MaterialVariant.objects.get(material_var_id)
                data["item_variant"] = item
                data["is_product"] = False
            except MaterialVariant.DoesNotExist:
                raise serializers.ValidationError(
                    {"message": "Material Variant not found"}
                )
            return data

    from django.db import transaction

    @transaction.atomic
    def create(self, validated_data):

        request = self.context.get("request")
        user = request.user

        quantity = validated_data.get("quantity")
        item = validated_data.get("item_variant")
        is_product = validated_data.get("is_product")

        content_type = ContentType.objects.get_for_model(item.__class__)
        discount = item.product.discount if is_product else item.material.discount

        cart, cart_status = Cart.objects.get_or_create(user=user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            content_type=content_type,
            object_id=item.id,
            defaults={
                "quantity": quantity,
                "unit_price": item.final_price,
                "discount_amount": discount,
            },
        )

        if not created:
            cart_item.unit_price = item.final_price
            cart_item.discount_amount = discount
            cart_item.quantity += quantity
            cart_item.save(update_fields=["quantity", "unit_price", "discount_amount"])

            cart_item.refresh_from_db()  # This helps to have latest data from db,

        return cart_item
