from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessCategoryViewSet, BusinessViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'categories', BusinessCategoryViewSet)
router.register(r'products', ProductViewSet, basename='products')
router.register(r'', BusinessViewSet, basename='businesses')

urlpatterns = [
    path('', include(router.urls)),
]