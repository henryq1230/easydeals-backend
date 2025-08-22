import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class NotificationService:
    """Servicio básico para notificaciones"""
    
    def send_notification(
        self, 
        user, 
        title: str, 
        message: str, 
        notification_type: str = 'system',
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Enviar notificación básica"""
        try:
            from ..models import Notification
            
            # Crear notificación en la base de datos
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                data=data or {}
            )
            
            logger.info(f"Notification created: {notification.id}")
            
            return {
                'notification_id': notification.id,
                'success': True,
                'message': 'Notification sent successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }