from django.shortcuts import render
from rest_framework.views import APIView 
from cart.models import Cart,CartItem
from cart.serializers import CartItemSerializer,CartSerializer
from rest_framework.response import Response
from materials.models import Materials,MaterialVariant
from products.models import Products,ProductVariant
from rest_framework import status
from django.contrib.contenttypes.models import ContentType
from decimal import  Decimal
from rest_framework.permissions import AllowAny,IsAuthenticated
from core.permissions import IsAdminOrIsOwner, IsOwnerOrReadOnly 




class CartView(APIView):

# you will need to add guest logic for this at the frontend before you can make use of AllowAny.

    permission_classes = [AllowAny,]

    def get(self,request):

        user = request.user
        
        
        try:
            cart = Cart.objects.prefetch_related('items').get(user=user)
            
            cart.refresh_prices()
        except Cart.DoesNotExist:
            return Response('Cart Does not exist')

        random_products = Products.objects.filter(is_active=True)[:4]
        random_materials = Materials.objects.filter(is_active=True)[:4]
        
        data = {
                
            'order_summary' : {
                'total_items' : cart.cart_item_count,
                 'total_discount' : cart.cart_item_total_discount,
                 'Total_amount' : cart.cart_items_total_price,
                 },
                 
            'cart_items' : [{
                'id' : item.id,
                'image' : request.build_absolute_uri(item.content_object.images.filter(is_primary=True)),
                'name': item.content_object.product.name,
                'color' : item.content_object.color,
                'size' : item.content_object.size,
                'price' : item.unit_price,
                'total': item.sub_total,
                'quantity': item.quantity,
                'discount' : item.discount_amount,
                'percent_discount': item.percent_discount
            } for item in cart.items.all()],

            'random_products' : [
                {
                'id' : pdt.id,
                'image' : request.build_absolute_uri(pdt.variant.filter(is_active=True).first().images.filter(is_primary=True)),
                'name' : pdt.name,
                'price' : pdt.discounted_price,
                'discount' : pdt.discount,
                'percent_discount': getattr(pdt,'get_percent_discount',0),
                'review_count': getattr(pdt.reviews, 'get_review_count',0),
                'average_rating' : getattr(pdt,'get_item_average_rating',0),
            } for pdt in random_products],
            
            
            'random_materials' : [
                {
                'id' : mtl.id,
                'image' : request.build_absolute_uri(mtl.variant.filter(is_active=True).first().images.filter(is_primary=True)),
                'name' : mtl.name,
                'price' : mtl.discounted_price,
                'discount' : mtl.discount, 
                'percent_discount': getattr(mtl,'get_percent_discount',0),
                'review_count': getattr(mtl.reviews, 'get_review_count',0),
                'average_rating' : getattr(mtl,'get_item_average_rating',0)
            } for mtl in random_materials]
        }
        

        return Response(data)



class AddToCartView(APIView):

    permission_classes = [AllowAny,]

    def post(self,request):
        material_var_id = request.data.get('material_variant_id')
        product_var_id = request.data.get('product_variant_id')
        quantity = Decimal(str(request.data.get('quantity',1)))


        if not (material_var_id or product_var_id):
            return Response(
                {"message": "Either material_var_id or product_var_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if material_var_id and product_var_id:
            return Response(
                {"message": "Send only one: material_var_id or product_var_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # created = False
            # cart_item = None
            # cart_status = True

            # cart,cart_status = Cart.objects.get_or_create(user=request.user)


            # if material_var_id:
            #     item = MaterialVariant.objects.get(pk=material_var_id)
            #     content_type = ContentType.objects.get_for_model(MaterialVariant)

            #     cart_item,created = CartItem.objects.get_or_create(
            #         cart=cart,
            #         content_type=content_type,
            #         object_id = item.id,
            #         defaults={'quantity':quantity,'unit_price': item.price,'discount_amount': item.material.discount}  
            #     )

            # elif product_var_id:
            
            #     item = ProductVariant.objects.get(id=product_var_id)
            #     content_type = ContentType.objects.get_for_model(ProductVariant)

            #     cart_item,created = CartItem.objects.get_or_create(
            #         cart=cart,
            #         content_type = content_type,
            #         object_id = item.id,
            #         defaults={'quantity':quantity,'unit_price': item.final_price ,'discount_amount':item.product.discount}
            #     )

            # SHORTER METHOD O WRITE THE ABOVE DRY(Don't Repeat yourself) 
            
            cart,cart_status = Cart.objects.get_or_create(user=request.user)
            
            
            #  METHOD 1
            # if product_var_id:
            #     ModelClass = ProductVariant
            #     item_id = product_var_id
            #     is_product = True
            # else:
            #     ModelClass = MaterialVariant
            #     item_id = material_var_id
            #     is_product = False
            
            # METHOD 2 (tenary operation) ---- SHORTER
            ModelClass = ProductVariant if product_var_id else MaterialVariant
            item_id = product_var_id if product_var_id else material_var_id
            is_product = bool(product_var_id) # means is_produt s true for product_var_id and false for materal_var_id
                
            # 3. Fetch the item dynamically
            item = ModelClass.objects.get(id=item_id)
            content_type = ContentType.objects.get_for_model(ModelClass)
            
            
            cart, cart_status = Cart.objects.get_or_create(user=request.user)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                content_type=content_type,
                object_id=item.id,
                defaults={'quantity': quantity, 'unit_price': item.final_price}
            )

            if not created:
                cart_item.unit_price = item.price
                cart_item.quantity += Decimal(str(quantity))
                cart_item.discount_amount *= cart_item.quantity 
                cart_item.save()


            if cart_status or not cart.status:    
                cart.status = True
                cart.save()


            return Response({'message': 'Item added to cart successfully'}, status=status.HTTP_201_CREATED)    
      
        except ProductVariant.DoesNotExist:
            return Response({'message': 'Product Variant not found'}, status=status.HTTP_404_NOT_FOUND)
        except MaterialVariant.DoesNotExist:
            return Response({'message': 'Material Variant not found'}, status=status.HTTP_404_NOT_FOUND)            
        
            

class UpdateCartItemView(APIView):
    

    permission_classes = [IsAuthenticated,]
    
    def put(self,request,pk):

        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=pk, cart=cart)

            quantity = Decimal(str(request.data.get('quantity',1)))

            if quantity > 0:

                cart_item.quantity = quantity
                cart_item.save()
            else :
                cart_item.delete()

            return Response({'message':'Cart item updated successfully'}, status=status.HTTP_200_OK)    
        except CartItem.DoesNotExist:
            return Response({'message':'Cart Item not found'},status=status.HTTP_400_BAD_REQUEST)




class RemoveCartItemView(APIView):

    permission_classes = [IsAuthenticated,]

    def delete(self,request,pk):

        try:

            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'message':'CartItem not found'},status=status.HTTP_404_NOT_FOUND)
        cart_item.delete()
        cart.save()
            
        return Response({'message':'Cart Item deleted successfully'})    

