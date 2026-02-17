from django.contrib import admin
from order.models import OrderItem,Order,PaymentMethod,Address


class OrderAdmin(admin.ModelAdmin):

    list_display = ('user','shipping_address','total_items','delivery_method','total_amount','status','payment_method','payment_reference','delivery_status','payment_status','delivery_status')


class OrderItemAdmin(admin.ModelAdmin):

    list_display = ('item_type','item_name','quantity','unit_price','sub_total','discount_amount',)

    def item_name(self):
        object = self.get_object()
        return object.content_object.name
    
    def item_type(self):
        object = self.get_object()
        return object.content_type
    

class PaymentMethodAdmin(admin.ModelAdmin):

    list_dislpay = ()


class PaymentMethodAdmin(admin.ModelAdmin):

    list_display = ()


class Address(admin.ModelAdmin):

    list_display = ()


admin.site.register(Order,OrderAdmin)
admin.site.register(OrderItem,OrderItemAdmin)
