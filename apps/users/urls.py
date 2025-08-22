from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AddressViewSet, DriverProfileViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')
router.register(r'addresses', AddressViewSet, basename='addresses')
router.register(r'drivers', DriverProfileViewSet, basename='drivers')

urlpatterns = [
    path('', include(router.urls)),
]