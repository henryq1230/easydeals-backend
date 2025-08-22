from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, FCMTokenViewSet

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notifications')
router.register(r'tokens', FCMTokenViewSet, basename='fcm-tokens')

urlpatterns = [
    path('', include(router.urls)),
]