from django.db import models
from apps.orders.models import Order
from apps.users.models import User
import uuid

class DriverLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.OneToOneField(User, on_delete=models.CASCADE, related_name='current_location')
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    heading = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0-360 degrees
    speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # km/h
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # meters
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.driver.username} location"

class OrderTracking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='tracking')
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracking_orders')
    
    # Route information
    estimated_distance = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # km
    estimated_duration = models.IntegerField(null=True, blank=True)  # minutes
    route_polyline = models.TextField(blank=True)  # Encoded polyline from Google Maps
    
    pickup_time = models.DateTimeField(null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class LocationHistory(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_history')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='location_history', null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']