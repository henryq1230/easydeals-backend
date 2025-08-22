from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Order, Rating
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer, RatingSerializer
)
from apps.payments.services.tilopay_service import TilopayService
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'order_type']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'client':
            return Order.objects.filter(customer=user).order_by('-created_at')
        elif user.user_type == 'driver':
            return Order.objects.filter(driver=user).order_by('-created_at')
        elif user.user_type == 'business':
            return Order.objects.filter(business__owner=user).order_by('-created_at')
        elif user.user_type == 'admin':
            return Order.objects.all().order_by('-created_at')
        return Order.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        else:
            return OrderDetailSerializer
    
    def create(self, request):
        """Crear nueva orden con pago"""
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Crear orden
                order_data = self._prepare_order_data(serializer.validated_data, request.user)
                order = Order.objects.create(**order_data)
                
                # Crear items si los hay
                if serializer.validated_data.get('items'):
                    self._create_order_items(order, serializer.validated_data['items'])
                
                # Procesar pago si no es efectivo
                payment_method = serializer.validated_data['payment_method']
                if payment_method != 'cash':
                    payment_response = self._process_payment(order, payment_method, serializer.validated_data)
                    
                    response_serializer = OrderDetailSerializer(order)
                    response_data = response_serializer.data
                    response_data['payment'] = payment_response
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
                
                # Para efectivo, confirmar orden directamente
                order.status = 'confirmed'
                order.save()
                
                response_serializer = OrderDetailSerializer(order)
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Order creation failed: {e}")
                return Response({
                    'error': 'Error al crear la orden',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _prepare_order_data(self, validated_data, user):
        """Preparar datos para crear la orden"""
        from apps.businesses.models import Business, Product
        from apps.users.models import Address
        
        # Calcular totales
        items_data = validated_data.get('items', [])
        subtotal = sum(Decimal(str(item['quantity'])) * Decimal(str(item['unit_price'])) for item in items_data)
        
        # Obtener delivery fee del negocio o usar por defecto
        delivery_fee = Decimal('5.00')  # Por defecto
        if validated_data.get('business_id'):
            try:
                business = Business.objects.get(id=validated_data['business_id'])
                delivery_fee = business.delivery_fee
            except Business.DoesNotExist:
                pass
        
        tax = subtotal * Decimal('0.07')  # 7% ITBMS
        commission = subtotal * Decimal('0.15')  # 15% comisión
        total = subtotal + delivery_fee + tax
        
        return {
            'customer': user,
            'business_id': validated_data.get('business_id'),
            'order_type': validated_data['order_type'],
            'pickup_address_id': validated_data.get('pickup_address_id'),
            'delivery_address_id': validated_data['delivery_address_id'],
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'tax': tax,
            'commission': commission,
            'total': total,
            'notes': validated_data.get('notes', '')
        }
    
    def _create_order_items(self, order, items_data):
        """Crear items de la orden"""
        from .models import OrderItem
        from apps.businesses.models import Product
        
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product_id=item_data['product'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            )
    
    def _process_payment(self, order, payment_method, validated_data):
        """Procesar pago con Tilopay"""
        tilopay_service = TilopayService()
        
        try:
            if payment_method == 'tilopay_yappy':
                yappy_phone = validated_data.get('yappy_phone')
                payment_response = tilopay_service.create_yappy_payment(order, yappy_phone)
            else:  # tilopay_card
                payment_response = tilopay_service.create_card_payment(order)
            
            # Crear registro de pago
            from apps.payments.models import Payment
            Payment.objects.create(
                order=order,
                customer=order.customer,
                payment_method=payment_method,
                amount=order.total,
                tilopay_order_id=payment_response.get('order_id'),
                tilopay_payment_url=payment_response.get('payment_url'),
                status='pending'
            )
            
            return {
                'payment_url': payment_response.get('payment_url'),
                'order_id': payment_response.get('order_id'),
                'expires_at': payment_response.get('expires_at')
            }
            
        except Exception as e:
            logger.error(f"Payment processing failed for order {order.id}: {e}")
            raise Exception(f"Error al procesar pago: {e}")
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Actualizar estado de la orden"""
        order = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if not new_status:
            return Response({
                'error': 'Estado requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar permisos para cambiar estado
        if not self._can_update_status(request.user, order, new_status):
            return Response({
                'error': 'No tienes permisos para cambiar a este estado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Actualizar estado
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Registrar historial
            from .models import OrderStatusHistory
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user,
                notes=notes
            )
            
            logger.info(f"Order {order.id} status updated from {old_status} to {new_status}")
            
            serializer = OrderDetailSerializer(order)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Order status update failed: {e}")
            return Response({
                'error': 'Error al actualizar estado',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _can_update_status(self, user, order, new_status):
        """Verificar si el usuario puede cambiar el estado"""
        if user.user_type == 'admin':
            return True
        
        if user.user_type == 'business' and user == order.business.owner:
            return new_status in ['confirmed', 'preparing', 'ready', 'cancelled']
        
        if user.user_type == 'driver' and user == order.driver:
            return new_status in ['picked_up', 'on_the_way', 'delivered']
        
        if user.user_type == 'client' and user == order.customer:
            return new_status in ['cancelled']
        
        return False
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Calificar orden"""
        order = self.get_object()
        
        if order.status != 'delivered':
            return Response({
                'error': 'Solo se pueden calificar órdenes entregadas'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el usuario puede calificar esta orden
        if request.user != order.customer:
            return Response({
                'error': 'Solo el cliente puede calificar la orden'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                order=order,
                rater=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)