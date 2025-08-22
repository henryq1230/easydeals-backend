from django.db import models

# Create your models here.
from django.db import models
from apps.users.models import User
import uuid

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('order_update', 'Actualización de Pedido'),
        ('payment', 'Pago'),
        ('promotion', 'Promoción'),
        ('driver_assignment', 'Asignación de Conductor'),
        ('delivery', 'Entrega'),
        ('rating', 'Calificación'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    data = models.JSONField(default=dict, blank=True)  # Additional data (order_id, etc.)
    
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Firebase Cloud Messaging
    fcm_token = models.TextField(blank=True)
    fcm_response = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens')
    token = models.TextField(unique=True)
    device_id = models.CharField(max_length=100, blank=True)
    platform = models.CharField(max_length=10, choices=[('ios', 'iOS'), ('android', 'Android')], blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)