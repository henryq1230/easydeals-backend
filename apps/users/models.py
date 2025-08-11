from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    USER_TYPES = (
        ('client', 'Cliente'),
        ('driver', 'Conductor'),
        ('business', 'Negocio'),
        ('admin', 'Administrador'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='client')
    phone = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"

class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=100)  # Casa, Trabajo, etc.
    address_line = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Addresses'
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

class DriverProfile(models.Model):
    VEHICLE_TYPES = (
        ('car', 'Automóvil'),
        ('motorcycle', 'Motocicleta'),
        ('bicycle', 'Bicicleta'),
        ('walk', 'A pie'),
    )
    
    DOCUMENT_TYPES = (
        ('license', 'Licencia de Conducir'),
        ('id', 'Cédula'),
        ('vehicle_registration', 'Registro de Vehículo'),
        ('insurance', 'Seguro'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_profile')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    vehicle_brand = models.CharField(max_length=50, blank=True)
    vehicle_model = models.CharField(max_length=50, blank=True)
    vehicle_year = models.IntegerField(null=True, blank=True)
    license_plate = models.CharField(max_length=20, blank=True)
    is_available = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    completed_trips = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Driver: {self.user.username}"

class DriverDocument(models.Model):
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DriverProfile.DOCUMENT_TYPES)
    document_file = models.ImageField(upload_to='driver_documents/')
    is_verified = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)