from django.contrib import admin
from .models import DriverLocation, OrderTracking, LocationHistory

@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ('driver', 'latitude', 'longitude', 'speed', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('driver__username',)
    readonly_fields = ('updated_at',)

@admin.register(OrderTracking)
class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = ('order', 'driver', 'estimated_distance', 'estimated_duration', 'pickup_time', 'actual_arrival')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('order__order_number', 'driver__username')

@admin.register(LocationHistory)
class LocationHistoryAdmin(admin.ModelAdmin):
    list_display = ('driver', 'order', 'latitude', 'longitude', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('driver__username', 'order__order_number')
    readonly_fields = ('timestamp',)