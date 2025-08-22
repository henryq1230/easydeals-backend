from rest_framework import serializers
from .models import OrderTracking, DriverLocation
from apps.orders.models import Order
from apps.users.models import User

class OrderTrackingSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    customer_name = serializers.CharField(source='order.customer.get_full_name', read_only=True)
    driver_name = serializers.CharField(source='order.driver.get_full_name', read_only=True)
    
    class Meta:
        model = OrderTracking
        fields = [
            'id', 'order_id', 'order_status', 'status', 
            'latitude', 'longitude', 'notes', 'timestamp',
            'customer_name', 'driver_name'
        ]
        read_only_fields = ['id', 'timestamp']

class DriverLocationSerializer(serializers.ModelSerializer):
    driver_id = serializers.UUIDField(source='driver.id', read_only=True)
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    driver_phone = serializers.CharField(source='driver.phone', read_only=True)
    
    class Meta:
        model = DriverLocation
        fields = [
            'id', 'driver_id', 'driver_name', 'driver_phone',
            'latitude', 'longitude', 'is_active', 'last_updated'
        ]
        read_only_fields = ['id', 'driver_id', 'driver_name', 'driver_phone']

class LocationUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar ubicación"""
    order_id = serializers.UUIDField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)