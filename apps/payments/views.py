from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import json

from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer
from .services.tilopay_service import TilopayService

logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_method']
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'client':
            return Payment.objects.filter(customer=user).order_by('-created_at')
        elif user.user_type == 'business':
            return Payment.objects.filter(order__business__owner=user).order_by('-created_at')
        elif user.user_type == 'admin':
            return Payment.objects.all().order_by('-created_at')
        return Payment.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def create(self, request):
        """Crear nuevo pago"""
        serializer = PaymentCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                order = serializer.validated_data['order']
                payment_method = serializer.validated_data['payment_method']
                
                # Verificar que el usuario puede pagar esta orden
                if request.user != order.customer:
                    return Response({
                        'error': 'No puedes pagar esta orden'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Verificar que la orden no tenga un pago exitoso
                if Payment.objects.filter(order=order, status='completed').exists():
                    return Response({
                        'error': 'Esta orden ya fue pagada'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Crear pago
                payment = Payment.objects.create(
                    order=order,
                    customer=request.user,
                    payment_method=payment_method,
                    amount=order.total,
                    status='pending'
                )
                
                # Procesar pago según método
                if payment_method == 'cash':
                    payment.status = 'completed'
                    payment.save()
                    
                    # Actualizar orden
                    order.status = 'confirmed'
                    order.save()
                    
                elif payment_method in ['tilopay_card', 'tilopay_yappy']:
                    # Procesar con Tilopay
                    tilopay_service = TilopayService()
                    
                    if payment_method == 'tilopay_yappy':
                        yappy_phone = serializer.validated_data.get('yappy_phone')
                        if not yappy_phone:
                            return Response({
                                'error': 'Número de Yappy requerido'
                            }, status=status.HTTP_400_BAD_REQUEST)
                        
                        payment_response = tilopay_service.create_yappy_payment(order, yappy_phone)
                    else:
                        payment_response = tilopay_service.create_card_payment(order)
                    
                    # Actualizar pago con datos de Tilopay
                    payment.tilopay_order_id = payment_response.get('order_id')
                    payment.tilopay_payment_url = payment_response.get('payment_url')
                    payment.save()
                    
                    # Retornar URL de pago
                    response_data = PaymentSerializer(payment).data
                    response_data['payment_url'] = payment_response.get('payment_url')
                    response_data['expires_at'] = payment_response.get('expires_at')
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
                
                return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Payment creation failed: {e}")
                return Response({
                    'error': 'Error al procesar pago',
                    'details': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Procesar reembolso"""
        payment = self.get_object()
        
        # Verificar permisos
        if request.user.user_type not in ['admin'] and request.user != payment.order.business.owner:
            return Response({
                'error': 'No tienes permisos para reembolsar este pago'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if payment.status != 'completed':
            return Response({
                'error': 'Solo se pueden reembolsar pagos completados'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Si es pago de Tilopay, procesar reembolso
            if payment.payment_method in ['tilopay_card', 'tilopay_yappy']:
                tilopay_service = TilopayService()
                refund_response = tilopay_service.refund_payment(payment)
                
                payment.status = 'refunded'
                payment.save()
                
                return Response({
                    'message': 'Reembolso procesado exitosamente',
                    'refund_id': refund_response.get('refund_id')
                })
            else:
                # Para efectivo, solo marcar como reembolsado
                payment.status = 'refunded'
                payment.save()
                
                return Response({
                    'message': 'Pago marcado como reembolsado'
                })
                
        except Exception as e:
            logger.error(f"Refund failed for payment {payment.id}: {e}")
            return Response({
                'error': 'Error al procesar reembolso',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de pagos"""
        if request.user.user_type not in ['admin', 'business']:
            return Response({
                'error': 'No tienes permisos para ver estadísticas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        queryset = self.get_queryset()
        
        stats = {
            'total_payments': queryset.count(),
            'completed_payments': queryset.filter(status='completed').count(),
            'pending_payments': queryset.filter(status='pending').count(),
            'failed_payments': queryset.filter(status='failed').count(),
            'refunded_payments': queryset.filter(status='refunded').count(),
            'total_amount': sum(p.amount for p in queryset.filter(status='completed')),
            'payment_methods': {}
        }
        
        # Estadísticas por método de pago
        for method in ['cash', 'tilopay_card', 'tilopay_yappy']:
            method_payments = queryset.filter(payment_method=method, status='completed')
            stats['payment_methods'][method] = {
                'count': method_payments.count(),
                'amount': sum(p.amount for p in method_payments)
            }
        
        return Response(stats)

@method_decorator(csrf_exempt, name='dispatch')
class TilopayWebhookView(viewsets.ViewSet):
    """Webhook para recibir notificaciones de Tilopay"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def webhook(self, request):
        """Procesar webhook de Tilopay"""
        try:
            # Log del webhook recibido
            logger.info(f"Tilopay webhook received: {request.body}")
            
            # Parsear datos
            webhook_data = json.loads(request.body)
            order_id = webhook_data.get('order_id')
            status = webhook_data.get('status')
            
            if not order_id or not status:
                return HttpResponse("Missing required fields", status=400)
            
            # Buscar pago
            try:
                payment = Payment.objects.get(tilopay_order_id=order_id)
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for Tilopay order ID: {order_id}")
                return HttpResponse("Payment not found", status=404)
            
            # Actualizar estado del pago
            if status == 'completed':
                payment.status = 'completed'
                payment.save()
                
                # Actualizar orden
                payment.order.status = 'confirmed'
                payment.order.save()
                
                logger.info(f"Payment {payment.id} completed via webhook")
                
            elif status == 'failed':
                payment.status = 'failed'
                payment.save()
                
                logger.info(f"Payment {payment.id} failed via webhook")
            
            return HttpResponse("OK", status=200)
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook")
            return HttpResponse("Invalid JSON", status=400)
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return HttpResponse("Internal error", status=500)