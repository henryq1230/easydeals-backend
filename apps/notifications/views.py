from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import logging

from .models import Notification, FCMToken
from .serializers import NotificationSerializer, FCMTokenSerializer
from .services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notification_type', 'is_read']
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marcar notificación como leída"""
        notification = self.get_object()
        
        if notification.user != request.user:
            return Response({
                'error': 'No puedes marcar esta notificación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Marcar todas las notificaciones como leídas"""
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated} notificaciones marcadas como leídas'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtener cantidad de notificaciones no leídas"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['delete'])
    def clear_old(self, request):
        """Eliminar notificaciones antiguas (más de 30 días)"""
        from datetime import timedelta
        
        old_date = timezone.now() - timedelta(days=30)
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            created_at__lt=old_date
        ).delete()
        
        return Response({
            'message': f'{deleted_count} notificaciones antiguas eliminadas'
        })
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Obtener notificaciones agrupadas por tipo"""
        notification_type = request.query_params.get('type')
        
        if not notification_type:
            return Response({
                'error': 'Parámetro "type" requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        notifications = self.get_queryset().filter(
            notification_type=notification_type
        )
        
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

class FCMTokenViewSet(viewsets.ModelViewSet):
    serializer_class = FCMTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return FCMToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Crear o actualizar token FCM"""
        token = serializer.validated_data['token']
        device_id = serializer.validated_data.get('device_id')
        
        # Verificar si ya existe el token
        existing_token = FCMToken.objects.filter(
            user=self.request.user,
            token=token
        ).first()
        
        if existing_token:
            # Actualizar token existente
            existing_token.device_id = device_id
            existing_token.is_active = True
            existing_token.save()
            return existing_token
        else:
            # Crear nuevo token
            return serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register_device(self, request):
        """Registrar dispositivo para notificaciones push"""
        serializer = FCMTokenSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            device_id = serializer.validated_data.get('device_id')
            
            try:
                # Crear o actualizar token
                fcm_token, created = FCMToken.objects.update_or_create(
                    user=request.user,
                    token=token,
                    defaults={
                        'device_id': device_id,
                        'is_active': True
                    }
                )
                
                # Desactivar otros tokens del mismo dispositivo
                if device_id:
                    FCMToken.objects.filter(
                        user=request.user,
                        device_id=device_id
                    ).exclude(
                        id=fcm_token.id
                    ).update(is_active=False)
                
                return Response({
                    'message': 'Dispositivo registrado exitosamente',
                    'token_id': fcm_token.id,
                    'created': created
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"FCM token registration failed: {e}")
                return Response({
                    'error': 'Error al registrar dispositivo',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def unregister_device(self, request):
        """Desregistrar dispositivo"""
        token = request.data.get('token')
        device_id = request.data.get('device_id')
        
        if not token and not device_id:
            return Response({
                'error': 'Token o device_id requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        query = FCMToken.objects.filter(user=request.user)
        
        if token:
            query = query.filter(token=token)
        if device_id:
            query = query.filter(device_id=device_id)
        
        updated = query.update(is_active=False)
        
        return Response({
            'message': f'{updated} dispositivos desregistrados'
        })
    
    @action(detail=False, methods=['post'])
    def test_notification(self, request):
        """Enviar notificación de prueba"""
        if request.user.user_type != 'admin':
            return Response({
                'error': 'Solo administradores pueden enviar notificaciones de prueba'
            }, status=status.HTTP_403_FORBIDDEN)
        
        message = request.data.get('message', 'Notificación de prueba')
        target_user_id = request.data.get('user_id')
        
        try:
            notification_service = NotificationService()
            
            if target_user_id:
                # Enviar a usuario específico
                from apps.users.models import User
                target_user = User.objects.get(id=target_user_id)
                
                result = notification_service.send_notification(
                    user=target_user,
                    title='Notificación de Prueba',
                    message=message,
                    notification_type='system',
                    data={'test': True}
                )
            else:
                # Enviar a usuario actual
                result = notification_service.send_notification(
                    user=request.user,
                    title='Notificación de Prueba',
                    message=message,
                    notification_type='system',
                    data={'test': True}
                )
            
            return Response({
                'message': 'Notificación de prueba enviada',
                'result': result
            })
            
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            return Response({
                'error': 'Error al enviar notificación de prueba',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de notificaciones"""
        if request.user.user_type != 'admin':
            return Response({
                'error': 'Solo administradores pueden ver estadísticas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from apps.users.models import User
        
        stats = {
            'total_users': User.objects.count(),
            'users_with_tokens': FCMToken.objects.filter(is_active=True).values('user').distinct().count(),
            'total_active_tokens': FCMToken.objects.filter(is_active=True).count(),
            'total_notifications_sent': Notification.objects.count(),
            'notifications_by_type': {},
            'tokens_by_platform': {}
        }
        
        # Notificaciones por tipo
        from django.db.models import Count
        notification_types = Notification.objects.values('notification_type').annotate(
            count=Count('notification_type')
        )
        for item in notification_types:
            stats['notifications_by_type'][item['notification_type']] = item['count']
        
        return Response(stats)