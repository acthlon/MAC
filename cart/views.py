from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from cart.serializers import AddToCartSeralizer, CartItemSerializer
from materials.models import Materials, MaterialVariant
from products.models import Products, ProductVariant


class CartView(APIView):
    # you will need to add guest logic for this at the frontend before you can make use of AllowAny.

    permission_classes = [
        AllowAny,
    ]  # NOTE: change to IsAuthentcated

    def get(self, request):

        user = request.user

        try:
            cart = Cart.objects.prefetch_related("items").get(user=user)

            cart.refresh_prices()
        except Cart.DoesNotExist:
            return Response(
                {"message": "Cart Does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        # NOTE: To be moved nto utils folder nto a method
        random_products_qs = Products.objects.filter(is_active=True)[:4]
        random_materials_qs = Materials.objects.filter(is_active=True)[:4]

        random_products = []
        random_materials = []
        for item_k in list(random_products_qs) + list(random_materials_qs):
            model_name = None
            item = None

            if item_k.model_name == "products" or item_k.model_name == "materials":
                model_name = item_k.model_name
                item = item_k

            # item_model = item.model_name
            # item = item if item_model == 'products' else item

            item_variant = item.variants.filter(is_active=True).first()
            variant_image_obj = (
                item_variant.images.filter(is_primary=True).first()
                if item_variant
                else None
            )

            item_data = {
                "id": item.id,
                "image": request.build_absolute_uri(variant_image_obj.image.url)
                if variant_image_obj and variant_image_obj.image
                else None,  # NOTE:
                "name": item.name,
                "price": item.discounted_price,
                "discount": item.discount,
                "percent_discount": getattr(item, "get_percent_discount", 0),
                "review_count": getattr(item.reviews, "get_review_count", 0),
                "average_rating": getattr(item, "get_item_average_rating", 0),
            }

            random_materials.append(
                item_data
            ) if model_name == "materials" else random_products.append(item_data)

        data = {
            "order_summary": {
                "total_items": cart.cart_item_count,
                "total_discount": cart.cart_item_total_discount,
                "Total_amount": cart.cart_items_total_price,
            },
            "cart_items": [
                {
                    "id": item.id,
                    "image": request.build_absolute_uri(
                        item.content_object.images.filter(is_primary=True)
                        .first()
                        .image.url
                    )
                    if item.content_object
                    and item.content_object.images.filter(is_primary=True).exists()
                    else None,
                    "name": item.content_object.product.name
                    if item.content_type.model == "productvariant"
                    else item.content_object.material.name,
                    "color": item.content_object.color,
                    "size": item.content_object.size
                    if item.content_type.model == "productvariant"
                    else None,
                    "price": item.unit_price,
                    "total": item.sub_total,
                    "quantity": item.quantity,
                    "discount": item.discount_amount,
                    "percent_discount": item.percent_discount,
                }
                for item in cart.items.all()
            ],
            "random_products": random_products,
            "random_materials": random_materials,
        }

        return Response(data, status=status.HTTP_200_OK)


class AddToCartView(APIView):
    permission_classes = [
        AllowAny,
    ]

    def post(self, request):
        material_var_id = request.data.get("material_variant_id")
        product_var_id = request.data.get("product_variant_id")
        quantity = Decimal(str(request.data.get("quantity", 1)))

        if not (material_var_id or product_var_id):
            return Response(
                {"message": "Either material_var_id or product_var_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if material_var_id and product_var_id:
            return Response(
                {"message": "Send only one: material_var_id or product_var_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from django.db import transaction

            with transaction.atomic():
                cart, cart_status = Cart.objects.get_or_create(user=request.user)

                # METHOD 2 (tenary operation) ---- SHORTER
                ModelClass = ProductVariant if product_var_id else MaterialVariant
                item_id = product_var_id if product_var_id else material_var_id
                is_product = bool(
                    product_var_id
                )  # means is_produt s true for product_var_id and false for materal_var_id

                # 3. Fetch the item dynamically
                item = ModelClass.objects.get(id=item_id)
                content_type = ContentType.objects.get_for_model(ModelClass)

                # Fetch Prices and Discount
                discount = (
                    item.product.discount if is_product else item.material.discount
                )

                cart, cart_status = Cart.objects.get_or_create(user=request.user)

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
                    cart_item.save()

                if cart_status or not cart.status:
                    cart.status = True
                    cart.save()

                return Response(
                    {"message": "Item added to cart successfully"},
                    status=status.HTTP_201_CREATED,
                )

        except ProductVariant.DoesNotExist:
            return Response(
                {"message": "Product Variant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except MaterialVariant.DoesNotExist:
            return Response(
                {"message": "Material Variant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class AddToCart(generics.CreateAPIView):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = AddToCartSeralizer

    def get_serializer_context(self):
        request = self.request
        context = self.get_serializer_context()

        context["request"] = request
        return context


class UpdateCartItemView(generics.UpdateAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CartItemSerializer

    queryset = CartItem.objects.all()

    def get_object(self):

        user = self.request.user
        pk = self.kwargs.get("pk")
        queryset = self.get_queryset()

        cart = get_object_or_404(Cart, user=user)

        cart_item = get_object_or_404(queryset, id=pk, cart=cart)
        return cart_item

    # def put(self,request,pk):

    #     try:
    #         cart = Cart.objects.get(user=request.user)
    #         cart_item = CartItem.objects.get(id=pk, cart=cart)

    #         quantity = Decimal(str(request.data.get('quantity',1)))

    #         if quantity > 0:

    #             cart_item.quantity = quantity
    #             cart_item.save()
    #         else :
    #             cart_item.delete()

    #         return Response({'message':'Cart item updated successfully'}, status=status.HTTP_200_OK)
    #     except CartItem.DoesNotExist:
    #         return Response({'message':'Cart Item not found'},status=status.HTTP_400_BAD_REQUEST)


class RemoveCartItemView(generics.DestroyAPIView):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CartItemSerializer
    queryset = CartItem.objects.all()

    def get_object(self):

        queryset = self.get_queryset()

        user = self.request.user
        pk = self.kwargs.get("pk")
        cart = get_object_or_404(user=user)

        cart_item = get_object_or_404(queryset, cart=cart, id=pk)
        return cart_item

    # def delete(self,request,pk):

    #     try:

    #         cart = Cart.objects.get(user=request.user)
    #         cart_item = CartItem.objects.get(id=pk, cart=cart)
    #     except CartItem.DoesNotExist:
    #         return Response({'message':'CartItem not found'},status=status.HTTP_404_NOT_FOUND)
    #     cart_item.delete()
    #     cart.save()

    #     return Response({'message':'Cart Item deleted successfully'})
