from django.db import models
import uuid
from accounts.models import CustomUser
from order.models import Order,PaymentMethod

from core.constants import PAYMENT_STATUS_CHOICES
from payments.choices import PaymentStatusChoices, PaymentCurrencyChoices


class Payment(models.Model):
    
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser,on_delete=models.PROTECT,related_name='payments')
    order = models.ForeignKey(Order,on_delete=models.PROTECT, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    currency = models.CharField(max_length=4,default=PaymentCurrencyChoices.NGN,choices=PaymentCurrencyChoices.choices)
    status=models.CharField(choices=PaymentStatusChoices.choices, max_length=20, default=PaymentStatusChoices.PENDING)
    reference = models.CharField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f'Payment {self.reference} for Order {self.order.id}'
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Payments' 