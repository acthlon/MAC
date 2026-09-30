from django.contrib import admin

from payments.models import Payment, PaymentMethod, ReturnRequest


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "status")


class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment_method_code",
        "amount",
        "currency",
        "status",
        "reference",
        "created_at",
        "updated_at",
        "masked_card",
    )

    # def get_readonly_fields(self, request, obj=None):
    #     if obj:
    #         return [field.name for field in self.model._meta.fields]
    #     return []

    def masked_card(self, obj):
        from utils.payments.payment import PaymentUtils  # isort: skip

        return PaymentUtils.masked_card(obj)

    masked_card.short_description = "Card Used"


class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = (
        "reason",
        "status",
        "approved_at",
        "processed_at",
        "admin_notes",
        "return_amount",
    )

    readonly_fields = ("approved_at", "processed_at", "return_amount")


admin.site.register(Payment, PaymentAdmin)
admin.site.register(ReturnRequest, ReturnRequestAdmin)
