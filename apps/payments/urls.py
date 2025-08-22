from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, TilopayWebhookView

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payments')
router.register(r'webhooks/tilopay', TilopayWebhookView, basename='tilopay-webhook')

urlpatterns = [
    path('', include(router.urls)),
]