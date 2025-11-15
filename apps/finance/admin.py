from django.contrib import admin
from .models import PaymentRequest, Payment


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'expected_amount', 'currency', 'status_display', 'created_at')
    search_fields = ('consultation__patient__first_name', 'consultation__patient__last_name')
    list_filter = ('currency',)

    def status_display(self, obj):
        return obj.status


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'amount', 'currency', 'method', 'paid_at', 'created_by')
    list_filter = ('method', 'currency')
    search_fields = ('reference',)
