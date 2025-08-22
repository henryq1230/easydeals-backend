from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, Rating
from apps.businesses.serializers import ProductSerializer
from apps.users.serializers import AddressSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=8, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'product_price',
                 'quantity', 'unit_price', 'total_price', 'special_instructions']
        read_only_fields = ['id', 'total_price']

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'status_display', 'changed_by', 'changed_by_name', 
                 'notes', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class OrderCreateSerializer(serializers.Serializer):
    order_type = serializers.ChoiceField(choices=Order.ORDER_TYPES)
    business_id = serializers.UUIDField(required=False, allow_null=True)
    pickup_address_id = serializers.UUIDField(required=False, allow_null=True)
    delivery_address_id = serializers.UUIDField()
    items = OrderItemSerializer(many=True, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=['tilopay_card', 'tilopay_yappy', 'cash'])
    yappy_phone = serializers.CharField(required=False, allow_blank=True)  # Para Yappy
    
    def validate(self, attrs):
        order_type = attrs['order_type']
        
        if order_type == 'delivery':
            if not attrs.get('business_id'):
                raise serializers.ValidationError("business_id es requerido para pedidos de delivery")
            if not attrs.get('items'):
                raise serializers.ValidationError("items son requeridos para pedidos de delivery")
        
        if order_type == 'transport':
            if not attrs.get('pickup_address_id'):
                raise serializers.ValidationError("pickup_address_id es requerido para transporte")
            if attrs.get('items'):
                raise serializers.ValidationError("Los pedidos de transporte no pueden tener items")
        
        # Validar Yappy phone si es necesario
        if attrs.get('payment_method') == 'tilopay_yappy' and not attrs.get('yappy_phone'):
            raise serializers.ValidationError("yappy_phone es requerido para pagos con Yappy")
        
        return attrs

class OrderListSerializer(serializers.ModelSerializer):
    """Serializer para listado de órdenes (información básica)"""
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_logo = serializers.ImageField(source='business.logo', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'business_name', 'business_logo', 
                 'customer_name', 'driver_name', 'order_type', 'order_type_display',
                 'status', 'status_display', 'total', 'created_at', 'estimated_delivery_time']

class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de orden (información completa)"""
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    business_phone = serializers.CharField(source='business.phone', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    driver_phone = serializers.CharField(source='driver.phone', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)
    pickup_address = AddressSerializer(read_only=True)
    delivery_address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer', 'customer_name', 'customer_phone',
                 'business', 'business_name', 'business_phone', 'driver', 'driver_name', 
                 'driver_phone', 'order_type', 'order_type_display', 'status', 'status_display', 
                 'pickup_address', 'delivery_address', 'subtotal', 'delivery_fee', 'tax', 
                 'commission', 'total', 'notes', 'items', 'status_history', 'created_at', 
                 'estimated_delivery_time', 'delivered_at']
        read_only_fields = ['id', 'order_number', 'customer', 'created_at']

class RatingSerializer(serializers.ModelSerializer):
    rater_name = serializers.CharField(source='rater.get_full_name', read_only=True)
    
    class Meta:
        model = Rating
        fields = ['id', 'order', 'rating_type', 'rater', 'rater_name', 'rated_user', 
                 'rated_business', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'rater', 'created_at']
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5")
        return value