import logging
from typing import Dict, Any, Optional
from django.conf import settings
from ..models import Notification, FCMToken

logger = logging.getLogger(__name__)

class NotificationService:
    """Servicio para enviar notificaciones push y locales"""
    
    def __init__(self):
        self.fcm_enabled = hasattr(settings, 'FCM_SERVER_KEY') and settings.FCM_SERVER_KEY
        
    def send_notification(
        self, 
        user, 
        title: str, 
        message: str, 
        notification_type: str = 'system',
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enviar notificación a un usuario
        
        Args:
            user: Usuario destinatario
            title: Título de la notificación
            message: Mensaje de la notificación
            notification_type: Tipo de notificación
            data: Datos adicionales
            
        Returns:
            Dict con resultado del envío
        """
        try:
            # Crear notificación en la base de datos
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data or {}
            )
            
            result = {
                'notification_id': notification.id,
                'database_saved': True,
                'push_sent': False,
                'push_errors': []
            }
            
            # Enviar notificación push si está habilitado
            if self.fcm_enabled:
                push_result = self._send_push_notification(user, title, message, data)
                result.update(push_result)
            else:
                logger.info("FCM not configured, skipping push notification")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {
                'notification_id': None,
                'database_saved': False,
                'push_sent': False,
                'error': str(e)
            }
    
    def _send_push_notification(
        self, 
        user, 
        title: str, 
        message: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enviar notificación push via FCM"""
        try:
            # Obtener tokens activos del usuario
            tokens = FCMToken.objects.filter(user=user, is_active=True)
            
            if not tokens.exists():
                return {
                    'push_sent': False,
                    'push_errors': ['No active FCM tokens found']
                }
            
            # En un entorno real, aquí usarías la biblioteca de Firebase
            # Por ahora, simulamos el envío
            success_count = 0
            errors = []
            
            for token in tokens:
                try:
                    # Simular envío de notificación push
                    # En producción reemplazar con:
                    # from pyfcm import FCMNotification
                    # push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
                    # result = push_service.notify_single_device(...)
                    
                    logger.info(f"Push notification sent to token {token.token[:20]}...")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send push to token {token.id}: {e}")
                    errors.append(f"Token {token.id}: {str(e)}")
                    
                    # Desactivar token si es inválido
                    if 'invalid' in str(e).lower():
                        token.is_active = False
                        token.save()
            
            return {
                'push_sent': success_count > 0,
                'tokens_sent': success_count,
                'push_errors': errors
            }
            
        except Exception as e:
            logger.error(f"Push notification service error: {e}")
            return {
                'push_sent': False,
                'push_errors': [str(e)]
            }
    
    def send_bulk_notification(
        self, 
        user_ids: list, 
        title: str, 
        message: str, 
        notification_type: str = 'system',
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enviar notificación a múltiples usuarios"""
        from apps.users.models import User
        
        results = {
            'total_users': len(user_ids),
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        users = User.objects.filter(id__in=user_ids)
        
        for user in users:
            try:
                result = self.send_notification(user, title, message, notification_type, data)
                if result.get('database_saved'):
                    results['success_count'] += 1
                else:
                    results['error_count'] += 1
                    results['errors'].append(f"User {user.id}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                results['error_count'] += 1
                results['errors'].append(f"User {user.id}: {str(e)}")
        
        return results
    
    def send_order_notification(self, order, notification_type: str, custom_message: str = None):
        """Enviar notificación relacionada con una orden"""
        try:
            # Determinar destinatarios según el tipo de notificación
            recipients = []
            
            if notification_type in ['order_created', 'order_confirmed']:
                recipients.append(order.customer)
                if hasattr(order, 'business') and order.business:
                    recipients.append(order.business.owner)
            elif notification_type in ['order_assigned', 'order_picked_up']:
                recipients.extend([order.customer, order.driver])
            elif notification_type == 'order_delivered':
                recipients.extend([order.customer, order.driver])
                if hasattr(order, 'business') and order.business:
                    recipients.append(order.business.owner)
            
            # Mensajes predeterminados
            messages = {
                'order_created': f'Nueva orden #{order.id} creada',
                'order_confirmed': f'Orden #{order.id} confirmada',
                'order_assigned': f'Conductor asignado a orden #{order.id}',
                'order_picked_up': f'Orden #{order.id} recogida',
                'order_delivered': f'Orden #{order.id} entregada'
            }
            
            title = "Actualización de Orden"
            message = custom_message or messages.get(notification_type, f'Orden #{order.id} actualizada')
            
            # Enviar a cada destinatario
            results = []
            for recipient in recipients:
                result = self.send_notification(
                    user=recipient,
                    title=title,
                    message=message,
                    notification_type='order',
                    data={
                        'order_id': str(order.id),
                        'order_status': order.status,
                        'action_type': notification_type
                    }
                )
                results.append(result)
            
            return {
                'success': True,
                'recipients_count': len(recipients),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Failed to send order notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }