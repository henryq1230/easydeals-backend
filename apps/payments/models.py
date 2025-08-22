from django.db import models
from apps.orders.models import Order
from apps.users.models import User
import uuid

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('tilopay_card', 'Tarjeta (Tilopay)'),
        ('tilopay_yappy', 'Yappy (Tilopay)'),
        ('cash', 'Efectivo'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
        ('cancelled', 'Cancelado'),
        ('expired', 'Expirado'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Tilopay specific fields
    tilopay_transaction_id = models.CharField(max_length=100, blank=True)
    tilopay_order_id = models.CharField(max_length=100, blank=True, unique=True)
    tilopay_session_token = models.TextField(blank=True)
    tilopay_redirect_url = models.URLField(blank=True)
    tilopay_payment_url = models.URLField(blank=True)  # URL para redirigir al usuario
    
    # Yappy specific (via Tilopay)
    yappy_phone = models.CharField(max_length=15, blank=True)  # Teléfono para Yappy
    yappy_qr_code = models.TextField(blank=True)  # QR code data si aplica
    
    # Split payment data for Tilopay
    split_payment_data = models.JSONField(default=dict, blank=True)
    split_responses = models.JSONField(default=dict, blank=True)  # Respuestas de cada split
    
    # Generic payment fields
    external_transaction_id = models.CharField(max_length=100, blank=True)
    payment_data = models.JSONField(default=dict, blank=True)
    
    # Webhook and callback info
    webhook_received = models.BooleanField(default=False)
    webhook_data = models.JSONField(default=dict, blank=True)
    webhook_attempts = models.IntegerField(default=0)
    
    # Timing fields
    payment_initiated_at = models.DateTimeField(null=True, blank=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment {self.get_payment_method_display()} for Order #{self.order.order_number}"

class TilopaySubmerchant(models.Model):
    """Modelo para gestionar subcomercios en Tilopay"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tilopay_submerchant')
    submerchant_key = models.CharField(max_length=100, unique=True)
    business_name = models.CharField(max_length=200)
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=15)
    
    # Estado del submerchant
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=50, default='pending')
    
    # Información para split payments
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=4, default=0.15)  # 15%
    
    # Configuración de métodos de pago
    accepts_cards = models.BooleanField(default=True)
    accepts_yappy = models.BooleanField(default=True)
    
    # Información de Tilopay
    tilopay_response_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Submerchant: {self.business_name}"

class Commission(models.Model):
    COMMISSION_TYPES = (
        ('platform', 'Plataforma'),
        ('driver', 'Conductor'),
        ('business', 'Negocio'),
    )
    
    COMMISSION_STATUS = (
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'), 
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('reversed', 'Reversado'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='commissions')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_commissions')
    commission_type = models.CharField(max_length=20, choices=COMMISSION_TYPES)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_commissions')
    
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=4)
    status = models.CharField(max_length=20, choices=COMMISSION_STATUS, default='pending')
    
    # Tilopay split payment info
    tilopay_submerchant = models.ForeignKey(TilopaySubmerchant, on_delete=models.CASCADE, null=True, blank=True)
    tilopay_split_id = models.CharField(max_length=100, blank=True)
    tilopay_split_status = models.CharField(max_length=50, blank=True)
    
    # Payment method used
    payment_method_used = models.CharField(max_length=20, blank=True)  # card, yappy, etc.
    
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Commission {self.commission_type} - {self.amount}"

class PaymentAttempt(models.Model):
    """Registro de intentos de pago para análisis"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='attempts')
    payment_method = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    error_message = models.TextField(blank=True)
    tilopay_response = models.JSONField(default=dict, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attempt {self.payment_method} - {self.status}"