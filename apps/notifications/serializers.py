from rest_framework import serializers
from .models import Notification, FCMToken

class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'data', 'is_read', 'created_at', 'read_at', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'time_ago']
    
    def get_time_ago(self, obj):
        """Calcular tiempo transcurrido desde la creación"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "Hace unos segundos"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"Hace {minutes} minuto{'s' if minutes != 1 else ''}"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"Hace {hours} hora{'s' if hours != 1 else ''}"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"Hace {days} día{'s' if days != 1 else ''}"
        else:
            return obj.created_at.strftime("%d/%m/%Y")

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['id', 'token', 'device_id', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_token(self, value):
        """Validar formato del token FCM"""
        if not value or len(value) < 10:
            raise serializers.ValidationError("Token FCM inválido")
        return value

class NotificationCreateSerializer(serializers.Serializer):
    """Serializer para crear notificaciones manualmente"""
    title = serializers.CharField(max_length=255)
    message = serializers.CharField(max_length=1000)
    notification_type = serializers.ChoiceField(choices=[
        ('order', 'Orden'),
        ('payment', 'Pago'),
        ('promotion', 'Promoción'),
        ('system', 'Sistema')
    ])
    data = serializers.JSONField(required=False)
    target_user_id = serializers.UUIDField(required=False)

class NotificationStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de notificaciones"""
    total_users = serializers.IntegerField()
    users_with_tokens = serializers.IntegerField()
    total_active_tokens = serializers.IntegerField()
    total_notifications_sent = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    tokens_by_platform = serializers.DictField()