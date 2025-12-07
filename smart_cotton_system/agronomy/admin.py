from django.contrib import admin
from .models import Field, SensorLog, SeedVariety

@admin.register(SeedVariety)
class SeedVarietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'expected_yield')

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    # Убрали lat/lon, добавили seed_variety
    list_display = ('name', 'owner', 'seed_variety', 'irrigation_active')

@admin.register(SensorLog)
class SensorLogAdmin(admin.ModelAdmin):
    list_display = ('field', 'soil_moisture', 'weather_temp', 'timestamp')