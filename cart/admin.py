from django.contrib import admin
from cart.models import Cart,CartItem
from django.contrib.contenttypes.models import ContentType
from products.models import Products
from materials.models import Materials


class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_code','status')


class CartItemAdmin(admin.ModelAdmin):
    list_display = ('content_type','quantity','unit_price','sub_total','discount_amount')

    def formfield_for_foreignkey(self,db_field,request,**kwargs):
         
        if db_field.name == 'content_type':
            
            allowed_models = ContentType.objects.get_for_models(Products,Materials)
            
            kwargs['queryset'] = ContentType.objects.filter(pk__in = [ct.id for ct in allowed_models.values()])

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)    