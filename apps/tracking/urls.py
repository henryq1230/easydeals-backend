from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderTrackingViewSet, DriverLocationViewSet

router = DefaultRouter()
router.register(r'orders', OrderTrackingViewSet, basename='order-tracking')
router.register(r'drivers', DriverLocationViewSet, basename='driver-location')

urlpatterns = [
    path('', include(router.urls)),
]