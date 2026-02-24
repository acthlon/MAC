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
from django.db.models import Prefetch,Sum


class AddressView(APIView):

    permission_classes = [IsAuthenticated,]

    def post(self,request):
        try:
            serializer = AddressSerializer(data=request.data,context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)    
        
    def put(self,request,pk):    

        user = request.user

        address = get_object_or_404(Address,user=user,id=pk)
        
        serializer = AddressSerializer(address,data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class OrderListView(APIView):

    permission_classes = [IsAuthenticated,]

    def get(self,request):

        user = request.user
        try:
            order = Order.objects.filter(user=user).order_by('-created_at')
        except Exception as e:
            return Response({'message':str(e)},status=status.HTTP_400_BAD_REQUEST)
        
        serializer = OrderListSerializer(order,many=True)
        
        return Response(serializer.data)        


class OrderDetailsView(APIView):

    permission_classes = [IsAuthenticated,]

    def get(self,request,pk):

        user=request.user
        order = get_object_or_404(Order, id=pk, user=user)

        serializer = OrderDetailSerializer(order)
        
        return Response(serializer.data)
        


class CheckoutPreviewAPIView(APIView):

    permission_classes = [IsAuthenticated,]

    def get(self,request):
        
        user = request.user
        cart = Cart.objects.filter(user=user, status=True).prefetch_related(Prefetch('items', queryset=CartItem.objects.select_related('content_type'))).first()
        addresses = Address.objects.filter(user=user)
        payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('display_order')
        delivery_method = DeliveryMethod.objects.filter(is_active=True).order_by('display_order')

        order_summary = []

        if cart:
            sub_total = cart.items.aggregate(total=Sum('sub_total'))['total'] or Decimal('0.00')

            total_item = cart.items.aggregate(total=Sum('quantity'))['total'] or  0

            total = sub_total

            order_summary.append({ 

                'sub_total': sub_total,
                'total_item' : total_item,
                'delivery_fee' : None,
                'total' : total,
                'delivery_fee_note': 'Delivery fee will be added after you select an option'    
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
            # billing_address = serializer.validated_data['billing_address_id'],
            delivery_method = serializer.validated_data['delivery_method'],
            status = 'CREATED',
            payment_method = serializer.validated_data['payment_method'],
            payment_status = 'PENDING',
            delivery_status = 'PENDING',
            is_active = True
        )

        cart = get_object_or_404(Cart,user=user,status=True)

        if not cart.items.exists():
            return Response({'message':'Your Cart is empty'})

        for cart_item in cart.items.select_related('content_type').all():

            item = cart_item.content_object

            if cart_item.quantity > item.stock:
                return Response({'message':f'Not enough stock for {item.name} \n available: {item.stock}'})

            unit_price = item.price    
            discount_amount = item.discount


            OrderItem.objects.create(

                order = order,
                content_type = cart_item.content_type, 
                object_id = cart_item.object_id,
                content_object = item,
                quantity = cart_item.quantity,
                unit_price = unit_price,
                discount_amount = discount_amount,

            )
            
            # this should be calculated after the payment status has been confirmed
             
            # item.stock -= cart_item.quantity
            # item.save()

        order.save()
        cart.status = True
        cart.save()
        return Response('order created successfully')



class InitializePaymentAPIView(APIView):

    # def post(self,request,pk):
    pass


class PaymentCallbackAPIView(APIView):

    # def get(self,request):
    pass
