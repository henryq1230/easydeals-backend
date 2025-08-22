import requests
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TilopayService:
    def __init__(self):
        self.base_url = settings.TILOPAY_BASE_URL
        self.api_key = settings.TILOPAY_API_KEY
        self.secret_key = settings.TILOPAY_SECRET_KEY
        self.platform_key = settings.TILOPAY_PLATFORM_KEY
    
    def create_split_payment(self, order, payment_method: str, customer_phone: str = None) -> Dict[str, Any]:
        """
        Crear pago con split usando Tilopay (Card o Yappy)
        payment_method: 'tilopay_card' o 'tilopay_yappy'
        """
        try:
            payment_amount = float(order.total)
            split_data = self.calculate_split_amounts(order)
            
            # Configurar método de pago específico
            payment_config = self._get_payment_method_config(payment_method, customer_phone)
            
            payload = {
                "currency": "USD",
                "amount": payment_amount,
                "details": f"Pedido #{order.order_number} - EasyDeals",
                "orderId": str(order.id),
                "redirect_url": f"{settings.FRONTEND_URL}/payment/success?order_id={order.id}",
                "cancel_url": f"{settings.FRONTEND_URL}/payment/cancel?order_id={order.id}",
                "webhook_url": f"{settings.BACKEND_URL}/api/payments/tilopay/webhook/",
                "capture": True,
                "split": split_data,
                "customer": {
                    "name": f"{order.customer.first_name} {order.customer.last_name}",
                    "email": order.customer.email,
                    "phone": order.customer.phone
                },
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),  # Expira en 1 hora
                **payment_config  # Agregar configuración específica del método de pago
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'X-Platform-Key': self.platform_key
            }
            
            response = requests.post(
                f"{self.base_url}/v2/orders",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Tilopay split payment created successfully for order {order.id} with method {payment_method}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Tilopay split payment creation failed for order {order.id}: {e}")
            raise Exception(f"Failed to create Tilopay payment: {e}")
    
    def _get_payment_method_config(self, payment_method: str, customer_phone: str = None) -> Dict[str, Any]:
        """Configuración específica por método de pago"""
        if payment_method == 'tilopay_yappy':
            config = {
                "payment_methods": ["yappy"],
                "yappy_config": {
                    "phone": customer_phone,
                    "auto_redirect": True
                }
            }
        elif payment_method == 'tilopay_card':
            config = {
                "payment_methods": ["card"],
                "card_config": {
                    "save_card": False,
                    "capture": True
                }
            }
        else:
            config = {
                "payment_methods": ["card", "yappy"]  # Ambos métodos disponibles
            }
        
        return config
    
    def create_yappy_payment(self, order, customer_phone: str) -> Dict[str, Any]:
        """Crear pago específico para Yappy"""
        return self.create_split_payment(order, 'tilopay_yappy', customer_phone)
    
    def create_card_payment(self, order) -> Dict[str, Any]:
        """Crear pago específico para tarjetas"""
        return self.create_split_payment(order, 'tilopay_card')
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verificar firma del webhook de Tilopay"""
        try:
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def get_payment_status(self, tilopay_order_id: str) -> Dict[str, Any]:
        """Obtener estado de pago desde Tilopay"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'X-Platform-Key': self.platform_key
            }
            
            response = requests.get(
                f"{self.base_url}/v2/orders/{tilopay_order_id}",
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get payment status for {tilopay_order_id}: {e}")
            raise Exception(f"Failed to get payment status: {e}")
    
    def refund_payment(self, tilopay_order_id: str, amount: float = None, reason: str = None) -> Dict[str, Any]:
        """Crear reembolso en Tilopay"""
        try:
            payload = {
                "reason": reason or "Reembolso solicitado por cliente"
            }
            
            if amount:
                payload["amount"] = amount
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'X-Platform-Key': self.platform_key
            }
            
            response = requests.post(
                f"{self.base_url}/v2/orders/{tilopay_order_id}/refund",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refund payment {tilopay_order_id}: {e}")
            raise Exception(f"Failed to refund payment: {e}")
    
    def calculate_split_amounts(self, order) -> list:
        """
        Calcular montos para split payment con soporte para diferentes comisiones
        """
        total_amount = float(order.total)
        split_data = []
        
        # Comisión base de la plataforma (configurable por negocio)
        if order.business and hasattr(order.business.owner, 'tilopay_submerchant'):
            submerchant = order.business.owner.tilopay_submerchant
            platform_commission_rate = float(submerchant.commission_percentage)
        else:
            platform_commission_rate = 0.15  # 15% por defecto
        
        platform_commission = total_amount * platform_commission_rate
        business_amount = total_amount - platform_commission
        
        # Split para el negocio (recibe el monto menos la comisión de plataforma)
        if order.business and hasattr(order.business.owner, 'tilopay_submerchant'):
            split_data.append({
                "submerchant_key": order.business.owner.tilopay_submerchant.submerchant_key,
                "amount": round(business_amount, 2),
                "description": f"Venta - Pedido #{order.order_number}"
            })
        
        # Si hay conductor, calcular su comisión del delivery fee
        driver_commission = 0
        if order.driver and hasattr(order.driver, 'tilopay_submerchant') and order.delivery_fee > 0:
            driver_commission = float(order.delivery_fee) * 0.80  # 80% del delivery fee
            platform_commission -= driver_commission  # Reducir comisión de plataforma
            
            split_data.append({
                "submerchant_key": order.driver.tilopay_submerchant.submerchant_key,
                "amount": round(driver_commission, 2),
                "description": f"Delivery - Pedido #{order.order_number}"
            })
        
        # Split para la plataforma (comisión restante)
        split_data.append({
            "submerchant_key": settings.TILOPAY_PLATFORM_SUBMERCHANT_KEY,
            "amount": round(platform_commission, 2),
            "description": f"Comisión plataforma - Pedido #{order.order_number}"
        })
        
        logger.info(f"Split calculation for order {order.id}: {split_data}")
        return split_data
    
    def create_submerchant(self, user, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear submerchant en Tilopay"""
        try:
            payload = {
                "name": business_data['business_name'],
                "email": business_data['business_email'],
                "phone": business_data['business_phone'],
                "business_type": business_data.get('business_type', 'individual'),
                "country": "PA",  # Panamá
                "currency": "USD",
                "webhook_url": f"{settings.BACKEND_URL}/api/payments/tilopay/submerchant/webhook/"
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'X-Platform-Key': self.platform_key
            }
            
            response = requests.post(
                f"{self.base_url}/v2/submerchants",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create submerchant for user {user.id}: {e}")
            raise Exception(f"Failed to create submerchant: {e}")