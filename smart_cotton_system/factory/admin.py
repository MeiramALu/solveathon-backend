from django.contrib import admin
from .models import CottonBatch, Machine, MaintenanceLog

@admin.register(CottonBatch)
class CottonBatchAdmin(admin.ModelAdmin):
    # Используем поля, которые точно есть в новой модели
    list_display = ('batch_code', 'farmer', 'status', 'grade', 'created_at')
    search_fields = ('batch_code', 'farmer__username')
    list_filter = ('status', 'created_at') # harvest_date заменили на created_at

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'last_temp', 'is_active')

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('machine', 'timestamp', 'is_prediction', 'probability_failure')