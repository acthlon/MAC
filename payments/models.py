from django.db import models
import uuid
from accounts.models import CustomUser
from order.models import Order,PaymentMethod

from core.constants import PAYMENT_STATUS_CHOICES,REFUND_STATUS_CHOICES






class Payment(models.Model):
    
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser,on_delete=models.PROTECT,related_name='payments')
    order = models.ForeignKey(Order,on_delete=models.PROTECT, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    # NOTE: FOR THIS PROJECT YOU CAN STORE IN THE NORMAL DENOMINATION, 
    # FOR STORE LOWER DENOMINATION, IT WILL HELP DURING PRECISION 
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    currency = models.CharField(max_length=4,default='NGN')
    status=models.CharField(choices=PAYMENT_STATUS_CHOICES, max_length=20, default='pending')
    reference = models.CharField(max_length=100,blank=True,null=True), # NOTE: This should be unique 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True), # NOTE: Use choices for `card_brand` 
    card_bin = models.CharField(max_length=6, blank=True, null=True) # NOTE: NEVER STORE `CARD_PIN`
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    authorization_code = models.CharField(max_length=100, blank=True, null=True)
    
    
    
    @property
    def masked_card(self):
        """Returns something like: 408408******4081"""
        # NOTE: I DON'T THINK YOU NEED TO MASK THE CARD, JUST STORE THE LAST FOUR DIGITS,
        # WETIN YOU DEY STORE THE FULL CARD NUMBER, YOU WAN CHOP MY MONEY?
        if self.card_brand and self.card_last4:
            return f"{self.card_brand}******{self.card_last4}"
        return "N/A"
    
    
    
    def __str__(self):
        return f'Payment {self.reference} for Order {self.order.id}'
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Payments'
        
        

class RefundRequest(models.Model):
    
    order = models.ForeignKey(Order,on_delete=models.PROTECT, related_name='return_requests')
    user = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    reason = models.TextField(help_text="Reason for return (e.g. wrong size, damaged, etc.)")
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(auto_now=True,null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)

    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name_plural = "Return Requests"

    def __str__(self):
        return f"Return #{self.id} - Order #{self.order.id} ({self.status})"
