from django.contrib import admin
from .models import Vehicle, GPSLog, Route

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'driver', 'status')

@admin.register(GPSLog)
class GPSLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'timestamp', 'latitude', 'longitude')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'estimated_time', 'created_at')