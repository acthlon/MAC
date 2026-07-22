from django.contrib import admin

from products.models import (ProductImages, Products, ProductSpecification,
                             ProductVariant, ProductVideo)


class ProductImageInline(admin.TabularInline):
    model = ProductImages
    extra = 3

class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 1
    
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'categories', 'quality_category', 'description', 'price', 'slug', 'discount', 'is_active')
    search_fields = ('name', 'categories__name')
    inlines = [ProductVariantInline, ProductVideoInline]

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'size', 'color', 'stock', 'sku','price_adjustment')
    inlines = [ProductImageInline]

@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ('weight', 'material_type', 'product_line',)