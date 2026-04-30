from django.contrib import admin
from order.models import OrderItem,Order,PaymentMethod,Address,DeliveryMethod
from materials.models import Materials
from products.models import Products
from django.contrib.contenttypes.models import ContentType



class OrderAdmin(admin.ModelAdmin):

    list_display = ('user','shipping_address','total_items','delivery_method','total_amount','status','payment_method','payment_reference','delivery_status','payment_status','tracking_id','is_active')


class OrderItemAdmin(admin.ModelAdmin):

    list_display = ('item_type','item_name','quantity','unit_price','sub_total','discount_amount',)

    def item_name(self,obj):
        if obj.content_object:
            return obj.content_object.name
        return '-'
    
    def item_type(self,obj):
        return obj.content_type.model
    
    def formfield_for_foreignkey(self,db_field,request,**kwargs):

        if db_field.name == 'content_type':
            allowed_models = ContentType.objects.get_for_models(Materials,Products)

            kwargs["queryset"] = ContentType.objects.filter(pk__in = [ct.id for ct in allowed_models.values() ])
            
        return super().formfield_for_foreignkey(db_field,request,**kwargs)
    

class DeliveryMethodAdmin(admin.ModelAdmin):

    list_display = ('name','cost','description','estimated_date','is_active','is_displayed')


class PaymentMethodAdmin(admin.ModelAdmin):

    list_display = ('code','is_active')


class AddressAdmin(admin.ModelAdmin):

    list_display = ('id','user','phone_number','first_name','last_name','delivery_address','email','city','state','country','is_default','address_type')


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(DeliveryMethod, DeliveryMethodAdmin)