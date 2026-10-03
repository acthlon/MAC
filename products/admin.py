from django.contrib import admin

from products.models import (
    ProductImages,
    Products,
    ProductSpecification,
    ProductVariant,
    ProductVariantSize,
    ProductVideo,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImages
    extra = 0


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ProductVariantSizeInline(admin.TabularInline):
    model = ProductVariantSize
    extra = 0


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "categories",
        "quality_category",
        "description",
        "price",
        "slug",
        "discount",
        "status",
    )
    search_fields = ("name", "categories__name")
    inlines = [ProductVariantInline, ProductVideoInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "status",
        "color",
    )
    inlines = [ProductImageInline, ProductVariantSizeInline]


@admin.register(ProductImages)
class ProductImagesAdmin(admin.ModelAdmin):
    list_display = ("variant", "is_primary", "image")


@admin.register(ProductVariantSize)
class ProductSizesAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "size",
        "stock",
        "sku",
        "price_adjustment",
        "status",
    )


@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = (
        "weight",
        "material_type",
        "product_line",
    )
