from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from rest_framework import serializers
from rest_framework.reverse import reverse

from cart.models import Cart, CartItem
from core.choices import Status
from core.serializers import BaseCatalogCardSerializer
from materials.models import Materials, MaterialVariant
from products.models import Products, ProductVariant


class CartItemWriteSerializer(serializers.ModelSerializer):
    material_var_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    product_var_id = serializers.IntegerField(
        required=False, allow_null=True, write_only=True
    )
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate(self, data):
        request = self.context.get("request")
        material_var_id = request.data.get("material_var_id", None)
        product_var_id = request.data.get("product_var_id", None)
        quantity = Decimal(str(request.data.get("quantity", 1)))

        if not self.instance:
            if not (material_var_id or product_var_id):
                raise serializers.ValidationError(
                    {"message": "Either material_var_id or product_var_id is required"}
                )

            if material_var_id and product_var_id:
                raise serializers.ValidationError(
                    {"message": "Send only one: material_var_id or product_var_id"}
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        material_var_id = validated_data.pop("material_var_id", None)
        product_var_id = validated_data.pop("product_var_id", None)
        quantity = validated_data.pop("quantity", 1)

        user = self.context.get("request").user

        ModelClass = ProductVariant if product_var_id else MaterialVariant
        item_id = product_var_id if product_var_id else material_var_id

        try:
            item = ModelClass.objects.get(id=item_id)
        except ModelClass.DoesNotExist:
            raise serializers.ValidationError({"message": "Item is absent"})
        stock = getattr(item, "stock", 0)

        if item and stock < quantity:
            if stock == 0:
                raise serializers.ValidationError(
                    {"message": "Sorry, this item just sold out!"}
                )
            else:
                raise serializers.ValidationError(
                    {
                        "message": f"Cannot add to cart. Only {stock} items currently available in stock."
                    }
                )

        content_type = ContentType.objects.get_for_model(ModelClass)

        cart, cart_status = Cart.objects.get_or_create(user=user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            content_type=content_type,
            object_id=item.id,
            defaults={
                "quantity": quantity,
            },
        )

        if not created:
            locked_cart_item = CartItem.objects.select_for_update().get(id=cart_item.id)
            catalog_item_total_stock = getattr(
                locked_cart_item.content_object, "stock", None
            )
            catalog_item_remaining_stock = (
                catalog_item_total_stock - locked_cart_item.quantity
            )

            if quantity > catalog_item_remaining_stock:
                raise serializers.ValidationError(
                    {
                        "message": f"Cannot add item to cart. Only {catalog_item_total_stock} items currently available in stock and you have added {locked_cart_item.quantity} to cart already."
                    }
                )

            else:
                locked_cart_item.quantity += quantity
                locked_cart_item.save(update_fields=["quantity"])
                return locked_cart_item

        return cart_item

    def update(self, instance, validated_data):

        quantity = validated_data.pop("quantity", instance.quantity)

        catalog_item_total_stock = getattr(instance.content_object, "stock", None)

        if quantity > catalog_item_total_stock:
            raise serializers.ValidationError(
                {
                    "message": f"Cannot add to cart. Only {catalog_item_total_stock} items currently available in stock."
                }
            )

        instance.quantity = quantity
        instance.save(update_fields=["quantity"])

        return instance

    class Meta:
        model = CartItem
        fields = ("id", "quantity", "material_var_id", "product_var_id")


class CartItemSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(source="get_item_name")
    model_name = serializers.CharField(source="content_type.model", required=True)
    image = serializers.ImageField(source="get_item_image")
    color = serializers.CharField(source="content_object.color", allow_null=True)
    size = serializers.SerializerMethodField()
    actual_price = serializers.DecimalField(
        source="content_object.calculate_variant_actual_unit_price",
        required=True,
        allow_null=True,
        max_digits=10,
        decimal_places=2,
    )
    discounted_price = serializers.DecimalField(
        source="content_object.calculate_variant_discounted_price",
        required=True,
        allow_null=True,
        max_digits=10,
        decimal_places=2,
    )
    percent_discount = serializers.ReadOnlyField(
        source="content_object.calculate_variant_percent_discount",
        allow_null=True,
    )
    quantity = serializers.IntegerField(required=True)
    item_subtotal_price = serializers.SerializerMethodField()

    def get_item_subtotal_price(self, obj):
        from utils.cart.cart import CartItemUtils  # isort: skip

        return CartItemUtils.calculate_item_subtotal(obj)

    def get_size(self, obj):
        if not obj.content_object:
            return None

        if obj.content_type.model == "productvariant":
            return getattr(obj.content_object, "size", None)

        return None

    class Meta:
        model = CartItem
        fields = (
            "id",
            "name",
            "model_name",
            "image",
            "color",
            "size",
            "actual_price",
            "discounted_price",
            "percent_discount",
            "quantity",
            "item_subtotal_price",
        )


class CartSummarySerializer(serializers.Serializer):
    total_item_quantity = serializers.IntegerField(
        source="calculate_cart_total_item_count", required=True
    )
    cart_total_actual_price = serializers.DecimalField(
        required=True, max_digits=10, decimal_places=2
    )
    cart_total_discount = serializers.DecimalField(
        required=True, max_digits=10, decimal_places=2
    )
    cart_total_discounted_price = serializers.DecimalField(
        required=True, max_digits=10, decimal_places=2
    )


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(source="items", many=True)
    cart_summary = CartSummarySerializer(source="*", read_only=True)
    other_similar_items = serializers.SerializerMethodField()
    homepage_url = serializers.SerializerMethodField()

    def get_homepage_url(self, obj):
        request = self.context.get("request")
        url = reverse("home", request=request)
        return url

        return total_discount if total_discount else Decimal("0.00")

    def get_other_similar_items(self, obj):

        products = Products.objects.filter(status=Status.ACTIVE)[:4]
        materials = Materials.objects.filter(status=Status.ACTIVE)[:4]

        combined = list(products) + list(materials)
        combined_serialized = BaseCatalogCardSerializer(
            combined, context=self.context, many=True
        ).data
        return combined_serialized

    class Meta:
        model = Cart
        fields = (
            "cart_code",
            "cart_summary",
            "homepage_url",
            "cart_items",
            "other_similar_items",
        )
