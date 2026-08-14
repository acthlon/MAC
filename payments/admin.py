from django.contrib import admin

from payments.models import Payment, RefundRequest


class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment_method",
        "amount",
        "currency",
        "status",
        "reference",
        "created_at",
        "updated_at",
        "status",
    )

    def masked_card(self, obj):
        return obj.masked_card

    masked_card.short_description = "Card Used"


class RefundRequestAdmin(admin.ModelAdmin):
    list_display = (
        "reason",
        "status",
        "requested_at",
        "processed_at",
        "admin_notes",
        "refund_amount",
    )

    readonly_fields = ("requested_at", "processed_at", "refund_amount")


admin.site.register(Payment, PaymentAdmin)
admin.site.register(RefundRequest, RefundRequestAdmin)
