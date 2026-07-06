from django.db import models
from accounts.models import CustomUser
from materials.models import Materials
from products.models import Products  
from core.models import TimeStampModel
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from decimal import Decimal
from django.db.models import Sum

class Cart(TimeStampModel):


    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    cart_code = models.CharField(max_length=255, unique=True, blank=True)
    status = models.BooleanField(default='False')    


    @property
    def cart_items_total_price(self):
        
        # total_cart_price = 0
        # for item in self.items.all():
        #     item_price = item.sub_total
        #     total_cart_price += item_price
        # return total_cart_price     
        
        # SHORTER VERSION OF THE ABOVE CODE
        total_cart_price = self.items.aggregate(Sum('sub_total'))['sub_total__sum']

        return total_cart_price if total_cart_price else Decimal('0.00')

    @property
    def cart_item_total_discount(self):
        
        total_discount = self.items.aggregate(Sum('discount_amount'))['discount_amount__sum']
        return total_discount if total_discount else Decimal('0.00')

    @property
    def cart_item_count(self):
        return self.items.count()
    
    
    def refresh_prices(self):
        
        for item in self.items.all():
            variant = item.content_object 
            
            if not item:
                continue
            
            if item.content_type.model == 'products':    
                live_price = variant.final_price
                discount = variant.product.discounted_price
            
            if item.content_type.model == 'materials':    
                live_price = variant.final_price
                discount = variant.material.discounted_price
                
            if item.unit_price != live_price or item.discount_amount != discount:
                item.unit_price = live_price
                item.discount_amount = discount
                item.save()
    
    
    def save(self, *args, **kwargs):
        if not self.cart_code:
            self.cart_code = str(uuid.uuid4())
        super(Cart, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Carts'    
        ordering = ['-created_at']    

    def __str__(self):
        return f"{self.user.username}'s Cart with cartcode:{self.cart_code}"



class CartItem(TimeStampModel):

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type','object_id')

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,related_name='items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount =models.DecimalField(max_digits=12,decimal_places=2, default=0.00)


    @property
    def calculate_item_total(self):
            
            unit_price = self.unit_price
            discount_amount = self.discount_amount
            quantity = self.quantity
            sub_total = (unit_price - discount_amount) * quantity
            
            return sub_total.quantize(Decimal('0.00'))
    
    @property
    def percent_discount(self):
        
        percent_discount = (self.discount_amount / self.unit_price) * 100
        return percent_discount.quantize(Decimal('0.00'))
    
    
    def save(self,*args,**kwargs):

        self.sub_total = self.calculate_item_total

        super().save(*args,**kwargs)

    class Meta:
        verbose_name_plural = 'CartItems'    
        ordering = ['-created_at']        
            
    def __str__(self):
        return f"Cartitem in {self.cart.user.username}'s cart"          