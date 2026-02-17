from django.db import models
from accounts.models import CustomUser
from materials.models import Materials
from products.models import Products  
from core.models import TimeStampModel
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid
from decimal import Decimal


class Cart(TimeStampModel):


    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    cart_code = models.CharField(max_length=255, unique=True, blank=True)
    status = models.BooleanField(default='False')    


    def cart_total(self):

        total_cart_price = 0
        for item in self.items.all():

            item_price = item.sub_total
            total_cart_price += item_price

        return total_cart_price     

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


    def calculate_item_total(self):
            
            unit_price = Decimal(str(self.unit_price))
            discount_amount = Decimal(str(self.discount_amount))  
            quantity = Decimal(str(self.quantity))
            sub_total = (unit_price * quantity) - discount_amount
            return sub_total
    
    def save(self,*args,**kwargs):

        self.sub_total = self.calculate_item_total()

        super().save(*args,**kwargs)

    class Meta:
        verbose_name_plural = 'CartItems'    
        ordering = ['-created_at']        
            
    def __str__(self):
        return f"Cartitem in {self.cart.user.username}'s cart"          