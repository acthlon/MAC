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

    def save_model(self, request, obj, form, change):

        if change:
            # 1. Get the list of fields you actually changed on screen
            fields_to_update = set(form.changed_data)

            # 2. If you changed status to CONFIRMED, make sure tracking_id is saved too
            if "status" in fields_to_update and obj.status == "CONFIRMED":
                fields_to_update.add("tracking_id")

            # 3. If you changed delivery_status, make sure timestamps are saved too
            if "delivery_status" in fields_to_update:
                fields_to_update.update(
                    [
                        "status",
                        "delivered_at",
                        "shipped_at",
                        "out_for_delivery_at",
                        "canceled_at",
                        "failed_delivery_at",
                    ]
                )

            # 4. Keep only real database columns (prevents crashes)
            valid_columns = {f.name for f in obj._meta.fields}
            safe_fields = list(fields_to_update.intersection(valid_columns))
            # 5. Save only those fields!

            obj.save(update_fields=safe_fields)
        else:
            # New order created from admin: normal full save
            obj.save()


class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "item_type",
        "item_name",
        "quantity",
        "unit_price",
        "unit_discount",
        "sub_total",
        "total_discount",
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
