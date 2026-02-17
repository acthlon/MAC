from django.contrib import admin
from products.models import Products

class ProductAdmin(admin.ModelAdmin):

    list_display = ('name','description','price','image','category','slug','discount','is_active')
    search_fields = ('name','category')

admin.site.register(Products,ProductAdmin)