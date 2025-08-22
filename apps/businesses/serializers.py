from rest_framework import serializers
from .models import BusinessCategory, Business, BusinessHours, Product

class BusinessCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessCategory
        fields = ['id', 'name', 'icon', 'is_active']

class BusinessHoursSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = BusinessHours
        fields = ['id', 'day_of_week', 'day_name', 'open_time', 'close_time', 'is_closed']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'image', 
                 'is_available', 'preparation_time', 'created_at']
        read_only_fields = ['id', 'created_at']

class BusinessListSerializer(serializers.ModelSerializer):
    """Serializer para listado de negocios (menos información)"""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    categories_names = serializers.StringRelatedField(source='categories', many=True, read_only=True)
    
    class Meta:
        model = Business
        fields = ['id', 'name', 'description', 'service_type', 'logo', 'cover_image',
                 'rating', 'delivery_fee', 'minimum_order', 'estimated_delivery_time',
                 'owner_name', 'categories_names', 'is_verified', 'is_active']

class BusinessDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle de negocio (información completa)"""
    categories = BusinessCategorySerializer(many=True, read_only=True)
    hours = BusinessHoursSerializer(many=True, read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    
    class Meta:
        model = Business
        fields = ['id', 'owner', 'owner_name', 'name', 'description', 'service_type',
                 'categories', 'phone', 'email', 'address', 'latitude', 'longitude',
                 'logo', 'cover_image', 'is_verified', 'is_active', 'rating',
                 'delivery_fee', 'minimum_order', 'estimated_delivery_time',
                 'commission_rate', 'hours', 'products', 'created_at']
        read_only_fields = ['id', 'owner', 'rating', 'created_at']

class BusinessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['name', 'description', 'service_type', 'phone', 'email',
                 'address', 'latitude', 'longitude', 'logo', 'cover_image',
                 'delivery_fee', 'minimum_order', 'estimated_delivery_time']
    
    def validate_phone(self, value):
        if Business.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Este teléfono ya está registrado")
        return value