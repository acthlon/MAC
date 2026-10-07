from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from materials.models import MaterialVariant
from order.models import Address, DeliveryMethod, Order, OrderItem
from products.models import ProductVariantSize


class OrderAdmin(admin.ModelAdmin):
    # def get_readonly_fields(self, request, obj=None):
    #     # Automatically make every field read-only EXCEPT 'delivery_status'
    #     return [field.name for field in self.model._meta.fields if field.name != "delivery_status"]

    list_display = (
        "user",
        "order_number",
        "shipping_address_snapshot",
        "total_items",
        "delivery_method_name",
        "total_amount",
        "status",
        "payment_method_name",
        "payment_reference",
        "delivery_status",
        "payment_status",
        "tracking_id",
    )


class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "item_type",
        "item_name",
        "quantity",
        "unit_price",
        "sub_total",
        "discount",
        "total_amount",
    )

    @admin.display(description="Item Name")
    def item_name(self, obj):
        from utils.orders.order import OrderItemUtils  # isort: skip

        catalog_name = OrderItemUtils.catalog_name(obj)
        return catalog_name

    @admin.display(description="Item Type")
    def item_type(self, obj):
        return obj.content_type.model if obj.content_type else "-"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):

        if db_field.name == "content_type":
            allowed_models = ContentType.objects.get_for_models(
                MaterialVariant, ProductVariantSize
            )

            kwargs["queryset"] = ContentType.objects.filter(
                pk__in=[ct.id for ct in allowed_models.values()]
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class DeliveryMethodAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "cost",
        "description",
        "estimated_date",
        "status",
        "is_selected",
    )


class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "phone_number",
        "first_name",
        "last_name",
        "delivery_address",
        "email",
        "city",
        "state",
        "country",
        "is_default",
        "address_type",
    )


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(DeliveryMethod, DeliveryMethodAdmin)
