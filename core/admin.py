from django.contrib import admin

from core.forms import CategoryAdminForm
from core.models import Banner, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "target_model", "slug", "display_order", "status")
    list_filter = ("target_model", "status")

    class Media:
        js = ("admin/js/category_dynamic_form.js",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "target_model" and formfield:
            import json

            from core.choices import MaterialCategory, ProductCategory

            product_choices_json = json.dumps(
                [{"value": val, "label": lbl} for val, lbl in ProductCategory.choices]
            )
            material_choices_json = json.dumps(
                [{"value": val, "label": lbl} for val, lbl in MaterialCategory.choices]
            )
            formfield.widget.attrs.update(
                {
                    "data-product-choices": product_choices_json,
                    "data-material-choices": material_choices_json,
                }
            )
        return formfield


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle", "status")
