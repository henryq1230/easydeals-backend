from django.contrib import admin
from .models import Payment, TilopaySubmerchant, Commission, PaymentAttempt

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('tilopay_order_id', 'order', 'customer', 'payment_method', 'amount', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'webhook_received', 'created_at')
    search_fields = ('tilopay_order_id', 'order__order_number', 'customer__username')
    readonly_fields = ('created_at', 'updated_at', 'webhook_received')

@admin.register(TilopaySubmerchant)
class TilopaySubmerchantAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'submerchant_key', 'is_verified', 'is_active', 'commission_percentage')
    list_filter = ('is_verified', 'is_active', 'accepts_cards', 'accepts_yappy')
    search_fields = ('business_name', 'user__username', 'submerchant_key')

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('order', 'commission_type', 'recipient', 'amount', 'percentage', 'status', 'created_at')
    list_filter = ('commission_type', 'status', 'payment_method_used', 'created_at')
    search_fields = ('order__order_number', 'recipient__username')

@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ('payment', 'payment_method', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    readonly_fields = ('created_at',)