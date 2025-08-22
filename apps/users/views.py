from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import login
from rest_framework.authtoken.models import Token
from .models import User, Address, DriverProfile
from .serializers import (
    UserProfileSerializer, UserCreateSerializer, LoginSerializer,
    AddressSerializer, DriverProfileSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user_type', 'is_phone_verified']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    
    def get_queryset(self):
        if self.request.user.user_type == 'admin':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Registrar nuevo usuario"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'message': 'Usuario creado exitosamente. Verifica tu teléfono.',
                'user_id': str(user.id),
                'token': token.key,
                'user_type': user.user_type,
                'phone': user.phone
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Iniciar sesión"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            if not user.is_phone_verified:
                return Response({
                    'error': 'Teléfono no verificado',
                    'require_phone_verification': True,
                    'phone': user.phone
                }, status=status.HTTP_403_FORBIDDEN)
            
            token, created = Token.objects.get_or_create(user=user)
            login(request, user)
            
            return Response({
                'message': 'Inicio de sesión exitoso',
                'token': token.key,
                'user': UserProfileSerializer(user).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get', 'patch'])
    def profile(self, request):
        """Obtener o actualizar perfil del usuario actual"""
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = UserProfileSerializer(
                request.user, 
                data=request.data, 
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_phone(self, request):
        """Verificar teléfono con código SMS"""
        phone = request.data.get('phone')
        code = request.data.get('code')
        
        if not phone or not code:
            return Response({
                'error': 'Teléfono y código son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Aquí integrarías con servicio SMS real
        # Por ahora, código de prueba: 123456
        if code == '123456':
            try:
                user = User.objects.get(phone=phone)
                user.is_phone_verified = True
                user.save()
                
                return Response({
                    'message': 'Teléfono verificado exitosamente'
                })
            except User.DoesNotExist:
                return Response({
                    'error': 'Usuario no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'error': 'Código de verificación inválido'
            }, status=status.HTTP_400_BAD_REQUEST)

class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Establecer dirección como predeterminada"""
        address = self.get_object()
        
        # Remover default de otras direcciones
        Address.objects.filter(user=request.user).update(is_default=False)
        
        # Establecer como default
        address.is_default = True
        address.save()
        
        serializer = AddressSerializer(address)
        return Response(serializer.data)

class DriverProfileViewSet(viewsets.ModelViewSet):
    serializer_class = DriverProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'admin':
            return DriverProfile.objects.all()
        elif self.request.user.user_type == 'driver':
            return DriverProfile.objects.filter(user=self.request.user)
        return DriverProfile.objects.none()
    
    def perform_create(self, serializer):
        if self.request.user.user_type != 'driver':
            raise serializers.ValidationError("Solo conductores pueden crear perfil de conductor")
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """Cambiar disponibilidad del conductor"""
        profile = self.get_object()
        
        if request.user != profile.user:
            return Response({
                'error': 'No tienes permisos para esta acción'
            }, status=status.HTTP_403_FORBIDDEN)
        
        profile.is_available = not profile.is_available
        profile.save()
        
        return Response({
            'message': f"Disponibilidad {'activada' if profile.is_available else 'desactivada'}",
            'is_available': profile.is_available
        })