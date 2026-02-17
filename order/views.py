from rest_framework import status
from django.shortcuts import render,get_object_or_404
from cart.models import Cart,CartItem
from rest_framework.views import APIView
from order.models import Address,Order,OrderItem,DeliveryMethod,PaymentMethod
from order.serializers import AddressSerializer,OrderListSerializer,OrderDetailSerializer,PaymentMethodSerializer,DeliveryMethodSerializer,CreateOrderFromCartSerializer
from decimal import Decimal
from cart.serializers import CartItemSerializer
from django.db import models
from rest_framework.response import Response
from core.permissions import IsOwnerOrReadOnly,IsAdminOrIsOwner
from rest_framework.permissions import IsAuthenticated



class AddressView(APIView):

    permission_classes = [IsAuthenticated,]

    def post(self,request):
        try:
            serializer = AddressSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)    
        
    def put(self,request):    

        user = request.user
        try:
            address = Address.objects.get(user=user,status='active')
        except Exception as e:
            return Response({'message' : str(e)})    
        
        serializer = AddressSerializer(address,data=request.data, partial=True)

        if serializer.is_valid():
            return Response(serializer.data,status=status.HTTP_200_OK)



class OrderListView(APIView):

    permission_classes = [IsAuthenticated,]

    def get(self,request):

        user = request.user
        try:
            order = Order.objects.filter(user=user).order_by('-created_at')
        except Exception as e:
            return Response({'message':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        serializer = OrderListSerializer(order, context = {'request':request},many=True)

        if serializer.is_valid():
            return Response(serializer.data)        


class OrderDetailsView(APIView):

    permission_classes = [IsAuthenticated,]

    def get(self,request,pk):

        user=request.user
        order = get_object_or_404(Order, id=pk, user=user)

        serializer = OrderDetailSerializer(order, many=True, context = {'request':request})

        if serializer.is_valid():
            return Response(serializer.data)
        


class CheckoutPreviewAPIView(APIView):

    permission_classes = [IsAuthenticated,]

    def get(self,request):
        
        user = request.user
        cart = Cart.objects.filter(user=user, status='active').prefetch_related('items', queryset=CartItem.objects.select_related('content_type'))
        addresses = Address.objects.filter(user=user)
        payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('display_order')
        delivery_method = DeliveryMethod.objects.filter(is_active=True).order_by('display_order')

        order_summary = []

        if cart:
            total_amount = cart.items.aggregrate(total=models.Sum('sub_total'))['total__amounts'] or Decimal('0.00')

            total_item = cart.items.aggregrate(total=models.Sum('quantity'))['total__items'] or  0

            delivery_fee = cart.items.delivery_fee
            total = total_amount + delivery_fee 

            order_summary.append({

                'total_amount': total_amount,
                'total_item' : total_item,
                'delivery_fee' : delivery_fee,
                'total' : total

            })

        data = {
            'addresses' : AddressSerializer(addresses,many=True).data,
            'delivery_method' : DeliveryMethodSerializer(delivery_method, many=True).data,
            'payment_method' : PaymentMethodSerializer(payment_methods,many=True).data,
            'order_sumary' : order_summary,
            'cart_item_preview': CartItemSerializer(cart.items.all(),many=True).data
        }

        return Response(data,status=status.HTTP_200_OK)


class CreateOrderFromCartView(APIView):

    permission_classes = [IsAuthenticated,]

    def post(self,request):

        user = request.user

        serializer = CreateOrderFromCartSerializer(data=request.data, context={'request':request})

        if not serializer.is_valid():
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(
            
            user=user,
            shipping_address = serializer.validated_data['shipping_address_id'],
            billing_address = serializer.validated_data['billing_address_id'],
            status = 'pending',
            payment_method = serializer.validated_data['payment_method'],
            payment_status = 'pending',
            delivery_status = 'pending'
        )

        cart = get_object_or_404(Cart,user=user,status='active')

        if not cart.items.exists():
            return Response({'message':'Your Cart is empty'})

        for cart_item in cart.items.select_related('content_type').all():

            item = cart_item.content_object

            if cart_item.quantity > item.quantity:
                return Response({'message':f'Not enough stock for {item.name} \n available: {item.stock}'})

            unit_price = item.price    
            discount_amount = item.discount
            subtotal = unit_price - discount_amount

            OrderItem.objects.create(

                order = order,
                content_type = cart_item.content_type, 
                object_id = cart_item.object_id,
                content_object = item,
                quantity = cart_item.quantity,
                unit_price = unit_price,
                discount_amount = discount_amount,
                subtotal = subtotal
            )
            item.stock -= cart_item.quantity
            item.save()
        order.status = 'created'    
        order.save()
        cart.status = 'ordered'
        cart.save()

class InitializePaymentAPIView(APIView):

    # def post(self,request,pk):
    pass


class PaymentCallbackAPIView(APIView):

    # def get(self,request):
    pass
