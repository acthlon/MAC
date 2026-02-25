from django.contrib import admin
from payments.models import Payment


class PaymentAdmin(admin.ModelAdmin):
    
    list_display = ('id','payment_method', 'amount', 'currency', 'status', 'reference', 'created_at', 'updated_at')
    


admin.site.register(Payment,PaymentAdmin)    