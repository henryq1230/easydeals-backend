from rest_framework import serializers
from .models import Payment
from apps.orders.models import Order

class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    order_total = serializers.DecimalField(source='order.total', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order_id', 'customer_name', 'payment_method',
            'amount', 'order_total', 'status', 'tilopay_order_id',
            'tilopay_payment_url', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_id', 'customer_name', 'order_total',
            'tilopay_order_id', 'tilopay_payment_url', 'created_at', 'updated_at'
        ]

class PaymentCreateSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    yappy_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    class Meta:
        model = Payment
        fields = ['order', 'payment_method', 'yappy_phone']
    
    def validate(self, attrs):
        payment_method = attrs.get('payment_method')
        yappy_phone = attrs.get('yappy_phone')
        
        # Validar que si es Yappy, se proporcione el teléfono
        if payment_method == 'tilopay_yappy' and not yappy_phone:
            raise serializers.ValidationError({
                'yappy_phone': 'Número de teléfono requerido para pagos con Yappy'
            })
        
        return attrs

class PaymentStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de pagos"""
    total_payments = serializers.IntegerField()
    completed_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    refunded_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_methods = serializers.DictField()