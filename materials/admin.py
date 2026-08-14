from django.contrib import admin

from materials.models import (
    MaterialImages,
    Materials,
    MaterialSpecification,
    MaterialVariant,
    MaterialVideo,
)


class MaterialImageInline(admin.TabularInline):
    model = MaterialImages
    extra = 0


class MaterialVideoInline(admin.TabularInline):
    model = MaterialVideo
    extra = 0


class MaterialVariantInline(admin.TabularInline):
    model = MaterialVariant
    extra = 0


class MaterialSpecificationInline(admin.StackedInline):
    model = MaterialSpecification
    extra = 0


class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "categories",
        "quality_category",
        "specification",
        "description",
        "price",
        "slug",
        "discount",
        "status",
    )

    @admin.display(description="Specification")
    def specification(self, obj):
        if hasattr(obj, "specifications") and obj.specifications:
            return (
                obj.specifications.get_material_type_display()
                or obj.specifications.material_type
                or "View Specs"
            )
        return "-"

    search_fields = ("name", "category")

    inlines = [MaterialSpecificationInline, MaterialVariantInline, MaterialVideoInline]


@admin.register(MaterialVariant)
class MaterialVariantAdmin(admin.ModelAdmin):
    list_display = ("material", "status", "color", "stock", "sku", "price_adjustment")

    inlines = [MaterialImageInline]


admin.site.register(Materials, MaterialAdmin)  # 1st method of registring to the admin


@admin.register(MaterialSpecification)  # 2nd method of registring to the admin
class MaterialSpecificationAdmin(admin.ModelAdmin):
    list_display = ("id", "weight", "pattern", "width", "thread_count", "material_type")
