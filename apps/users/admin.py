from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address, DriverProfile, DriverDocument

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'user_type', 'is_phone_verified', 'date_joined')
    list_filter = ('user_type', 'is_phone_verified', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('EasyDeals Info', {
            'fields': ('user_type', 'phone', 'is_phone_verified', 'profile_image', 'date_of_birth')
        }),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'address_line', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('user__username', 'title', 'address_line')

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'is_available', 'is_verified', 'rating', 'completed_trips')
    list_filter = ('vehicle_type', 'is_available', 'is_verified')
    search_fields = ('user__username', 'license_plate')

@admin.register(DriverDocument)
class DriverDocumentAdmin(admin.ModelAdmin):
    list_display = ('driver', 'document_type', 'is_verified', 'uploaded_at')
    list_filter = ('document_type', 'is_verified', 'uploaded_at')    