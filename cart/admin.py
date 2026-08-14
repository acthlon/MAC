from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from cart.models import Cart, CartItem
from materials.models import MaterialVariant
from products.models import ProductVariant


class CartAdmin(admin.ModelAdmin):
    list_display = ("cart_code",)


class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "item_name",
        "content_type",
        "quantity",
        "unit_price",
        "sub_total",
        "discount_amount",
    )

    def item_name(self, obj):

        name = None
        if obj.content_type.model == "productvariant":
            name = obj.content_object.product.name

        elif obj.content_type.model == "materialvariant":
            name = obj.content_object.material.name

        return name

    item_name.short_description = "Item Name"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "content_type":
            allowed_models = ContentType.objects.get_for_models(
                ProductVariant, MaterialVariant
            )

            kwargs["queryset"] = ContentType.objects.filter(
                pk__in=[ct.id for ct in allowed_models.values()]
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
