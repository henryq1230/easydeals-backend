from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Address, DriverProfile, DriverDocument

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'title', 'address_line', 'latitude', 'longitude', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']

class DriverDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverDocument
        fields = ['id', 'document_type', 'document_file', 'is_verified', 'uploaded_at']
        read_only_fields = ['id', 'is_verified', 'uploaded_at']

class DriverProfileSerializer(serializers.ModelSerializer):
    documents = DriverDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = DriverProfile
        fields = ['vehicle_type', 'vehicle_brand', 'vehicle_model', 'vehicle_year',
                 'license_plate', 'is_available', 'is_verified', 'rating', 
                 'completed_trips', 'documents']
        read_only_fields = ['is_verified', 'rating', 'completed_trips']

class UserProfileSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)
    driver_profile = DriverProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'first_name', 'last_name',
                 'user_type', 'profile_image', 'date_of_birth', 'is_phone_verified',
                 'addresses', 'driver_profile', 'date_joined']
        read_only_fields = ['id', 'username', 'user_type', 'is_phone_verified', 'date_joined']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'password_confirm', 
                 'user_type', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        
        # Validar teléfono único
        if User.objects.filter(phone=attrs['phone']).exists():
            raise serializers.ValidationError("Este número de teléfono ya está registrado")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')
        
        if phone and password:
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                raise serializers.ValidationError('Credenciales inválidas')
            
            user = authenticate(username=user.username, password=password)
            
            if not user:
                raise serializers.ValidationError('Credenciales inválidas')
            
            if not user.is_active:
                raise serializers.ValidationError('Cuenta desactivada')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Debe proporcionar teléfono y contraseña')