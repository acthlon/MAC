from django.contrib import admin
from core.models import Category,Banner
from core.forms import CategoryAdminForm




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    
    form = CategoryAdminForm
    list_display = ('name', 'target_model','slug','display_order','is_active')
    list_filter = ('target_model', 'is_active')
    
    class Media:
        js = ('admin/js/category_dynamic_form.js',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == 'target_model' and formfield:
            import json
            from core.constants import PRODUCT_CATEGORY_CHOICES, MATERIAL_CATEGORY_CHOICES
            product_choices_json = json.dumps([{"value": val, "label": lbl} for val, lbl in PRODUCT_CATEGORY_CHOICES])
            material_choices_json = json.dumps([{"value": val, "label": lbl} for val, lbl in MATERIAL_CATEGORY_CHOICES])
            formfield.widget.attrs.update({
                'data-product-choices': product_choices_json,
                'data-material-choices': material_choices_json
            })
        return formfield
    
    
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    
    list_display = ('title','subtitle','is_active')
    