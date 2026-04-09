from django.db import models
from django.db.models import Sum,F,ExpressionWrapper,DecimalField
from cart.models import CartItem
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from accounts.models import CustomUser
from phonenumber_field.modelfields import PhoneNumberField 
from decimal import Decimal
from core.constants import PAYMENT_STATUS_CHOICES

ORDER_STATUS_CHOICES =[
    ('CREATED','Created'),
    ('CONFIRMED','Confirmed'),
    ('SHIPPED','Shipped'),
    ('COMPLETED','Completed'),
    ('CANCELED','Canceled'),
    ('FAILED','Failed'),
    ]


PAYMENT_METHOD_CHOICES = [
    ('PAYSTACK','Paystack'),
    ('CASH_ON_DELIVERY','Cash on Delivery'),
]

DELIVERY_STATUS_CHOICES =[
    ('PENDING','Pending'),
    ('PROCESSING','Processing'),
    ('OUT FOR DELIVERY','Out For Delivery'),
    ('DELIVERED','Delivered'),
    ('CANCELED','Canceled'),
    ('RETURNED','Returned'),
    ('FAILED DELIVERY','Failed Delivery'), 
    ]

ADDRESS_TYPE_CHOICES = [
    ('HOME','Home'),
    ('WORK','Work'),
    ('OTHERS','Others'),
]

DELIVERY_CHOICES = [
    ('STANDARD DELIVERY','Standard Delivery'),
    ('EXPRESS DELIVERY','Express Delivery'),
    ('PREMIUM DELIVERY', 'Premium Delivery'),
]




class Address(models.Model):

    id = models.UUIDField(unique=True,default=uuid.uuid4, editable=False,primary_key=True)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    phone_number = PhoneNumberField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    delivery_address = models.CharField(max_length=200)
    email = models.EmailField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)  
    country = models.CharField(max_length=100, default='Nigeria')
    additional_info = models.TextField(max_length=500, blank=True, null=True)
    is_default=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    address_type = models.CharField(choices=ADDRESS_TYPE_CHOICES, default='HOME')

    def save(self,*args,**kwargs):
        Address.objects.filter(user=self.user,is_default=True).exclude(id=self.id).update(is_default=False)
        
        super().save(*args,**kwargs)


    class Meta:
        verbose_name_plural = 'Addresses'    
        ordering = ['-is_default','-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.delivery_address}, {self.city}"



class DeliveryMethod(models.Model):


    name = models.CharField(max_length=255, choices=DELIVERY_CHOICES)
    description = models.CharField(max_length=255,null=True,blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_time = models.CharField(max_length=100)
    # estimated_date = models.CharField(max_length=100)
    # time_added = models.DateTimeField(aut_now_add=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_displayed = models.BooleanField(default=True)


    # def get_delivery_day(self):
    #     start_date = self.time_added

    #     if self.name == 'STANDARD_DELIVERY':
    #         completion_date1 = start_date + 5
    #         completion_date2 = start_date + 7
    #         delivery_day = f'{completion_date1} - {completion_date2}'
        
    #     elif self.name == 'EXPRESS_DELIVERY ':
    #         completion_date1 = start_date + 2
    #         completion_date2 = start_date + 3
    #         delivery_day = f'{completion_date1} - {completion_date2}'
        
    #     elif self.name == 'PREMIUM_DELIVERY':
    #         completion_date1 = start_date + 1

    #         delivery_day = f'Next business day - {completion_date1}'

    #     return delivery_day



    def save(self,*args,**kwargs):

        # self.estimated_date = self.get_delivery_day()
        super().save(*args,**kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['display_order','name']
        verbose_name_plural = "Delivery Methods"
        
        


class PaymentMethod(models.Model):

    id = models.UUIDField(unique=True,default=uuid.uuid4, editable=False,primary_key=True)
    code = models.CharField(max_length=50,unique=True,choices=PAYMENT_METHOD_CHOICES)
     
    display_name = models.CharField(max_length=100,help_text="Pay with Bank Cards - Paystack)",choices=PAYMENT_METHOD_CHOICES)
    description = models.TextField(blank=True,help_text="Short description under the name")
    icon = models.ImageField(upload_to='payment_icons/',blank=True,null=True)
 

    is_pre_pay = models.BooleanField(default=True)
    requires_registration = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Payment Methods"
        ordering = ['display_order', 'display_name']

    def __str__(self):
        return self.display_name

    @property
    def icon_url(self):
        if self.icon:
            return self.icon.url
        return None


class Order(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT, related_name= 'order')
    shipping_address = models.ForeignKey(Address, on_delete = models.PROTECT,related_name='ordered_shipped', null=True, blank=True)
    total_items = models.IntegerField()
    delivery_method = models.ForeignKey(DeliveryMethod,on_delete=models.PROTECT, related_name='order',null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    status = models.CharField(max_length = 30, choices= ORDER_STATUS_CHOICES, default='CREATED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT,null=True, blank=True,related_name='order_payment',)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES,default='PENDING')
    delivery_status = models.CharField(max_length=40,default='PENDING',choices=DELIVERY_STATUS_CHOICES)
    is_active = models.BooleanField(default = True)
    tracking_id = models.CharField(max_length=50, null=True,blank=True)



    @property
    def calculate_total_items(self):

        total_items = self.orderitems.aggregate(Sum('quantity'))['quantity__sum'] or 0
        return total_items


    @property
    def calculate_total_amount(self):

        total_amount_sum = self.orderitems.aggregate(
        total_amount=Sum
        (ExpressionWrapper(F('quantity') * F('unit_price') - F('discount_amount'), output_field=DecimalField(max_digits=12, decimal_places=2)))
                        )['total_amount'] or Decimal('0.00')


        # total_amount_sum = self.orderitems.aggregate(
        # total_amount=Sum
        # (ExpressionWrapper(F('sub_total'), output_field=DecimalField(max_digits=12, decimal_places=2)))
        #                 )['total_amount'] or Decimal('0.00')        

        delivery_fee = self.delivery_method.cost if self.delivery_method else Decimal('0.00')

        total_amount = total_amount_sum + delivery_fee
        return total_amount
    
    # @property
    # def get_payment_reference(self):
        
    #     ref = self.payment_method.display_name
    #     return ref

    def save(self,*args,**kwargs):
        if self.pk:
            self.total_amount = self.calculate_total_amount
            self.total_items = self.calculate_total_items

        if self.status == 'CONFIRMED':
            self.is_active = False    
        elif not self.status == 'COMPLETED':
            self.is_active = True
        
        # if self.payment_method:
        #     self.payment_reference = self.get_payment_reference 

        super().save(*args,**kwargs)



    class Meta:
        verbose_name_plural = 'Orders'    
        ordering = ['-created_at']  

    def __str__(self):
        return f'order {self.id} - {self.user.username}'
    


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderitems')
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type','object_id')

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2,editable=False)
    discount_amount =models.DecimalField(max_digits=10,
    decimal_places=2, default=0.00)


 
    def calculate_sub_total(self):
        sub_total = (self.quantity * self.unit_price) - self.discount_amount
        return sub_total
    
    
    def save(self,*args,**kwargs):
        self.sub_total = self.calculate_sub_total()
        super().save(*args,**kwargs)
        self.order.save()

    class Meta:
        unique_together = ['order','object_id','content_type']
        verbose_name_plural = 'Order Items'

    
    def __str__(self):
        return f"{self.quantity} × {self.content_object} in Order {self.order.id}"




# for the case of a model that is global (e.g DeliveryMethod, PaymentMethod), they don't need a user attribute, unlike a model whose object will be peculiar to each user (e.g Order, Address)  




# total = order.orderitems.aggregate(total=Sum(ExpressionWrapper(F('quantity') * F('unit_price') - F('discount_amount'),output_field=DecimalField())))['total']
# print("Calculated total:", total)
# print("Stored total:", order.total_amount)
