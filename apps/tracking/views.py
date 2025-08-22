from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
import logging

from .models import OrderTracking, DriverLocation
from .serializers import OrderTrackingSerializer, DriverLocationSerializer
from apps.orders.models import Order

logger = logging.getLogger(__name__)

class OrderTrackingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderTrackingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'client':
            return OrderTracking.objects.filter(order__customer=user).order_by('-timestamp')
        elif user.user_type == 'driver':
            return OrderTracking.objects.filter(order__driver=user).order_by('-timestamp')
        elif user.user_type == 'business':
            return OrderTracking.objects.filter(order__business__owner=user).order_by('-timestamp')
        elif user.user_type == 'admin':
            return OrderTracking.objects.all().order_by('-timestamp')
        return OrderTracking.objects.none()
    
    @action(detail=False, methods=['get'])
    def active_orders(self, request):
        """Obtener tracking de órdenes activas"""
        user = request.user
        
        # Estados considerados como activos
        active_statuses = ['confirmed', 'preparing', 'ready', 'picked_up', 'on_the_way']
        
        if user.user_type == 'client':
            orders = Order.objects.filter(
                customer=user,
                status__in=active_statuses
            )
        elif user.user_type == 'driver':
            orders = Order.objects.filter(
                driver=user,
                status__in=active_statuses
            )
        elif user.user_type == 'business':
            orders = Order.objects.filter(
                business__owner=user,
                status__in=active_statuses
            )
        else:
            return Response({
                'error': 'No tienes permisos para ver órdenes activas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener último tracking de cada orden
        tracking_data = []
        for order in orders:
            latest_tracking = OrderTracking.objects.filter(order=order).first()
            if latest_tracking:
                tracking_data.append(OrderTrackingSerializer(latest_tracking).data)
        
        return Response(tracking_data)
    
    @action(detail=False, methods=['post'])
    def update_location(self, request):
        """Actualizar ubicación de una orden (solo conductores)"""
        if request.user.user_type != 'driver':
            return Response({
                'error': 'Solo conductores pueden actualizar ubicación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        order_id = request.data.get('order_id')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if not all([order_id, latitude, longitude]):
            return Response({
                'error': 'order_id, latitude y longitude son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id, driver=request.user)
            
            # Crear tracking entry
            tracking = OrderTracking.objects.create(
                order=order,
                status=order.status,
                latitude=float(latitude),
                longitude=float(longitude),
                notes=f"Ubicación actualizada por conductor"
            )
            
            # Actualizar ubicación del conductor
            DriverLocation.objects.update_or_create(
                driver=request.user,
                defaults={
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'is_active': True,
                    'last_updated': timezone.now()
                }
            )
            
            serializer = OrderTrackingSerializer(tracking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Order.DoesNotExist:
            return Response({
                'error': 'Orden no encontrada o no asignada a ti'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({
                'error': 'Coordenadas deben ser números válidos'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Location update failed: {e}")
            return Response({
                'error': 'Error al actualizar ubicación',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DriverLocationViewSet(viewsets.ModelViewSet):
    serializer_class = DriverLocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'driver':
            return DriverLocation.objects.filter(driver=user)
        elif user.user_type == 'admin':
            return DriverLocation.objects.all()
        elif user.user_type in ['client', 'business']:
            # Clientes y negocios solo ven conductores activos
            return DriverLocation.objects.filter(is_active=True)
        return DriverLocation.objects.none()
    
    @action(detail=False, methods=['get'])
    def nearby_drivers(self, request):
        """Buscar conductores cercanos"""
        lat = request.query_params.get('latitude')
        lng = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 5)  # 5km por defecto
        
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
        
        # Búsqueda básica por proximidad
        lat_range = radius / 111.0  # Aproximación: 1 grado ≈ 111km
        lng_range = radius / (111.0 * abs(float(lat)))
        
        # Solo conductores activos en las últimas 5 minutos
        time_threshold = timezone.now() - timedelta(minutes=5)
        
        drivers = DriverLocation.objects.filter(
            is_active=True,
            last_updated__gte=time_threshold,
            latitude__range=[lat - lat_range, lat + lat_range],
            longitude__range=[lng - lng_range, lng + lng_range]
        )
        
        serializer = DriverLocationSerializer(drivers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def toggle_active(self, request):
        """Activar/desactivar disponibilidad del conductor"""
        if request.user.user_type != 'driver':
            return Response({
                'error': 'Solo conductores pueden cambiar su disponibilidad'
            }, status=status.HTTP_403_FORBIDDEN)
        
        location, created = DriverLocation.objects.get_or_create(
            driver=request.user,
            defaults={
                'latitude': 0.0,
                'longitude': 0.0,
                'is_active': False
            }
        )
        
        location.is_active = not location.is_active
        location.last_updated = timezone.now()
        location.save()
        
        return Response({
            'message': f"Disponibilidad {'activada' if location.is_active else 'desactivada'}",
            'is_active': location.is_active
        })