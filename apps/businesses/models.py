from django.db import models
from apps.users.models import User
import uuid

class BusinessCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = 'Business Categories'
    
    def __str__(self):
        return self.name

class Business(models.Model):
    SERVICE_TYPES = (
        ('food', 'Comida'),
        ('pharmacy', 'Farmacia'),
        ('grocery', 'Supermercado'),
        ('transport', 'Transporte'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')
    name = models.CharField(max_length=200)
    description = models.TextField()
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    categories = models.ManyToManyField(BusinessCategory, blank=True)
    
    # Contact Info
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    
    # Location
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    
    # Media
    logo = models.ImageField(upload_to='business_logos/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='business_covers/', null=True, blank=True)
    
    # Business Info
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    minimum_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    estimated_delivery_time = models.IntegerField(default=30)  # minutes
    
    # Commission
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.15)  # 15%
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class BusinessHours(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    )
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='hours')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('business', 'day_of_week')

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    preparation_time = models.IntegerField(default=15)  # minutes
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.business.name} - {self.name}"