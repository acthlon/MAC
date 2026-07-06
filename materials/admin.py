from django.contrib import admin
from materials.models import Materials,MaterialSpecification,MaterialImages, MaterialVideo,MaterialVariant


class MaterialImageInline(admin.TabularInline):
    model = MaterialImages
    extra = 3

class MaterialVideoInline(admin.TabularInline):
    model = MaterialVideo
    extra = 1


class MaterialVariantInline(admin.TabularInline):
    model = MaterialVariant
    extra = 3

class MaterialAdmin(admin.ModelAdmin):

    list_display = ('name','categories','quality_category','description','price','slug','discount','is_active')
    search_fields = ('name','category')
    
    inlines = [MaterialVariantInline,MaterialVideoInline]


@admin.register(MaterialVariant)
class MaterialVariantAdmin(admin.ModelAdmin):
    list_display = ('material', 'color', 'stock', 'sku','price_adjustment')
    
    inlines = [MaterialImageInline]


admin.site.register(Materials,MaterialAdmin)    # 1st method of registring to the admin


@admin.register(MaterialSpecification)         # 2nd method of registring to the admin
class MaterialSpecificationAdmin(admin.ModelAdmin):
    
    list_display = ('weight','pattern','width','thread_count','material_type')