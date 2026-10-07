from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from cart.models import Cart, CartItem
from materials.models import MaterialVariant
from products.models import ProductVariant


class CartAdmin(admin.ModelAdmin):
    list_display = ("get_cart_code",)

    def get_cart_code(self, obj):
        return f"{obj.user.username} Cart Code - {obj.cart_code}"

    get_cart_code.short_description = "Cart Code"


class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "item_name",
        "content_type",
        "quantity",
    )

    def item_name(self, obj):

        name = None
        if not obj.content_object:
            return "(Item no longer available)"

        if obj.content_type.model == "productvariantsize":
            name = obj.content_object.variant.product.name

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
