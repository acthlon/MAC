from django.shortcuts import render
from rest_framework.views import APIView 
from cart.models import Cart,CartItem
from cart.serializers import CartItemSerializer,CartSerializer
from rest_framework.response import Response
from materials.models import Materials
from products.models import Products
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

            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            # NOTE:  return Response({"message": "Cart Does not exist"})
            return Response('Cart Does not exist')

        serializer = CartSerializer(cart, context={'request':request})    
        return Response({'success': True,
                         'cart':serializer.data})



class AddToCartView(APIView):

    permission_classes = [AllowAny,]

    def post(self,request):
        material_id = request.data.get('material_id')
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity',1)

        if not (material_id or product_id):
            return Response(
                {"message": "Either material_id or product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if material_id and product_id:
            return Response(
                {"message": "Send only one: material_id or product_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            created = False
            cart_item = None
            cart_status = True

            cart,cart_status = Cart.objects.get_or_create(user=request.user)


            if material_id:
                item = Materials.objects.get(pk=material_id) # NOTE: CHECK IF MATERIAL STILL ACTIVE TOO
                content_type = ContentType.objects.get_for_model(Materials)

                cart_item,created = CartItem.objects.get_or_create(
                    cart=cart,
                    content_type=content_type,
                    object_id = item.id,
                    defaults={'quantity':quantity,'unit_price': item.price}  
                )

            elif product_id:
            
                item = Products.objects.get(id=product_id)
                content_type = ContentType.objects.get_for_model(Products)
            
                cart_item,created = CartItem.objects.get_or_create(
                    cart=cart,
                    content_type = content_type,
                    object_id = item.id,
                    defaults={'quantity':quantity,'unit_price': item.price}
                )
        

            if not created:
                cart_item.unit_price = item.price
                cart_item.quantity += Decimal(str(quantity))
                cart_item.save()


            if cart_status or not cart.status:    
                cart.status = True
                cart.save()


            return Response({'message':'item added to cart'},status=status.HTTP_201_CREATED)    

        except Materials.DoesNotExist:
            return Response({'message': 'Material not found'}, status=status.HTTP_404_NOT_FOUND)  
        except Products.DoesNotExist:
            return Response({'message': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)            

    

class UpdateCartItemView(APIView):
    

    permission_classes = [IsAuthenticated,]
    
    def put(self,request,pk):

        try:
            cart = Cart.objects.get(user=request.user)
            cart_item = CartItem.objects.get(id=pk, cart=cart)

            quantity = Decimal(str(request.data.get('quantity')))

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

