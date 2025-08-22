from django.contrib import admin
from .models import BusinessCategory, Business, BusinessHours, Product

@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'service_type', 'is_verified', 'is_active', 'rating', 'created_at')
    list_filter = ('service_type', 'is_verified', 'is_active', 'created_at')
    search_fields = ('name', 'owner__username', 'description')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'owner', 'description', 'service_type', 'categories')
        }),
        ('Contacto', {
            'fields': ('phone', 'email', 'address', 'latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('logo', 'cover_image')
        }),
        ('Configuración del Negocio', {
            'fields': ('is_verified', 'is_active', 'rating', 'delivery_fee', 'minimum_order', 'estimated_delivery_time', 'commission_rate')
        }),
    )

@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ('business', 'get_day_display', 'open_time', 'close_time', 'is_closed')
    list_filter = ('day_of_week', 'is_closed')
    
    def get_day_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_display.short_description = 'Día'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'price', 'category', 'is_available', 'preparation_time', 'created_at')
    list_filter = ('is_available', 'category', 'created_at')
    search_fields = ('name', 'business__name', 'description')