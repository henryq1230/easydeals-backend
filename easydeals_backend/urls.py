from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        'status': 'OK',
        'message': '🚀 EasyDeals Backend funcionando correctamente!',
        'version': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'health': '/api/health/',
            'users': '/api/users/',
            'businesses': '/api/businesses/',
            'orders': '/api/orders/',
            'tracking': '/api/tracking/',
            'payments': '/api/payments/',
            'notifications': '/api/notifications/'
        },
        'features': [
            'Autenticación con tokens',
            'Registro y login de usuarios',
            'Gestión de negocios y productos',
            'Sistema de órdenes completo',
            'Tracking en tiempo real',
            'Pagos con Tilopay',
            'Notificaciones push',
            'Geolocalización'
        ]
    })

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Health check
    path('api/health/', health_check),
    
    # API endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/businesses/', include('apps.businesses.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/tracking/', include('apps.tracking.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)