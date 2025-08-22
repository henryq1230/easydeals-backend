from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory, Rating

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('timestamp',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'business', 'driver', 'order_type', 'status', 'total', 'created_at')
    list_filter = ('order_type', 'status', 'created_at')
    search_fields = ('order_number', 'customer__username', 'business__name')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('order_number', 'customer', 'business', 'driver', 'order_type', 'status')
        }),
        ('Direcciones', {
            'fields': ('pickup_address', 'delivery_address')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'delivery_fee', 'tax', 'commission', 'total')
        }),
        ('Notas y Timing', {
            'fields': ('notes', 'estimated_delivery_time', 'delivered_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('order', 'rating_type', 'rater', 'rating', 'created_at')
    list_filter = ('rating_type', 'rating', 'created_at')
    search_fields = ('order__order_number', 'rater__username', 'comment')