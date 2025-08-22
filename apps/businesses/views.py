from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import BusinessCategory, Business, Product
from .serializers import (
    BusinessCategorySerializer, BusinessListSerializer, BusinessDetailSerializer,
    BusinessCreateSerializer, ProductSerializer
)

class BusinessCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BusinessCategory.objects.filter(is_active=True)
    serializer_class = BusinessCategorySerializer
    permission_classes = [AllowAny]

class BusinessViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['service_type', 'is_verified', 'is_active']
    search_fields = ['name', 'description', 'categories__name']
    ordering_fields = ['rating', 'created_at', 'delivery_fee']
    ordering = ['-rating']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'business':
            return Business.objects.filter(owner=user)
        elif user.user_type == 'admin':
            return Business.objects.all()
        else:
            # Clientes y conductores solo ven negocios activos y verificados
            return Business.objects.filter(is_active=True, is_verified=True)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BusinessCreateSerializer
        elif self.action == 'list':
            return BusinessListSerializer
        else:
            return BusinessDetailSerializer
    
    def perform_create(self, serializer):
        if self.request.user.user_type != 'business':
            raise serializers.ValidationError("Solo usuarios tipo 'business' pueden crear negocios")
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Obtener productos de un negocio"""
        business = self.get_object()
        products = Product.objects.filter(business=business, is_available=True)
        
        category = request.query_params.get('category')
        if category:
            products = products.filter(category=category)
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Cambiar estado activo/inactivo del negocio"""
        business = self.get_object()
        
        if request.user != business.owner and request.user.user_type != 'admin':
            return Response({
                'error': 'No tienes permisos para realizar esta acción'
            }, status=status.HTTP_403_FORBIDDEN)
        
        business.is_active = not business.is_active
        business.save()
        
        serializer = BusinessDetailSerializer(business)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Buscar negocios cercanos por coordenadas"""
        lat = request.query_params.get('latitude')
        lng = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 10)  # 10km por defecto
        
        if not lat or not lng:
            return Response({
                'error': 'Latitud y longitud son requeridas'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except ValueError:
            return Response({
                'error': 'Coordenadas deben ser números válidos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Búsqueda básica por proximidad (en producción usar PostGIS)
        lat_range = radius / 111.0  # Aproximación: 1 grado ≈ 111km
        lng_range = radius / (111.0 * abs(float(lat)))
        
        businesses = self.get_queryset().filter(
            latitude__range=[lat - lat_range, lat + lat_range],
            longitude__range=[lng - lng_range, lng + lng_range]
        )
        
        serializer = BusinessListSerializer(businesses, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'business':
            return Product.objects.filter(business__owner=user)
        elif user.user_type == 'admin':
            return Product.objects.all()
        else:
            return Product.objects.filter(is_available=True, business__is_active=True)
    
    def perform_create(self, serializer):
        if self.request.user.user_type != 'business':
            raise serializers.ValidationError("Solo dueños de negocio pueden crear productos")
        
        # Obtener el negocio del usuario
        try:
            business = Business.objects.get(owner=self.request.user)
            serializer.save(business=business)
        except Business.DoesNotExist:
            raise serializers.ValidationError("Debes tener un negocio registrado para crear productos")