from django.contrib import admin
from .models import Vehicle, GPSLog, Route, Field, Depot, OptimizationJob

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'driver', 'status', 'capacity', 'shift_minutes')
    list_filter = ('status',)

@admin.register(GPSLog)
class GPSLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'timestamp', 'latitude', 'longitude')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'estimated_time', 'created_at', 'is_active')
    list_filter = ('is_active',)

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'demand', 'service_time_minutes', 'is_active')
    list_filter = ('is_active',)

@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'is_default')
    list_filter = ('is_default',)

@admin.register(OptimizationJob)
class OptimizationJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'depot', 'created_at', 'status')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'request_data', 'ors_request', 'ors_solution')