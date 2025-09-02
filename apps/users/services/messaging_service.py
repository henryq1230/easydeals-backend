# apps/users/services/messaging_service.py
from twilio.rest import Client
from django.conf import settings
import logging
import random
import string

logger = logging.getLogger(__name__)

class MessagingService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_phone_number = settings.TWILIO_PHONE_NUMBER
        self.from_whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER

    def send_sms_verification(self, to_number, code):
        """Enviar código de verificación por SMS"""
        try:
            message_body = f"Tu código de verificación para Easy Deals es: {code}"
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_phone_number,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            return False

    def send_whatsapp_verification(self, to_number, code):
        """Enviar código de verificación por WhatsApp"""
        try:
            # Twilio requiere que el número tenga el prefijo 'whatsapp:'
            whatsapp_to = f"whatsapp:{to_number}"
            whatsapp_from = f"whatsapp:{self.from_whatsapp_number}"
            
            message_body = f"Tu código de verificación para Easy Deals es: *{code}*"
            message = self.client.messages.create(
                body=message_body,
                from_=whatsapp_from,
                to=whatsapp_to
            )
            logger.info(f"WhatsApp message sent to {to_number}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")
            return False

    def send_verification_code(self, to_number, code, method='sms'):
        """Enviar código de verificación por el método especificado"""
        if method == 'whatsapp':
            return self.send_whatsapp_verification(to_number, code)
        else:
            return self.send_sms_verification(to_number, code)

    @staticmethod
    def generate_verification_code(length=6):
        """Generar código de verificación aleatorio"""
        return ''.join(random.choices(string.digits, k=length))