from django.contrib import admin
from .models import CottonBatch, Machine, MaintenanceLog


@admin.register(CottonBatch)
class CottonBatchAdmin(admin.ModelAdmin):
    # В списке сразу видно: ID партии, Фермера и Итоговый класс
    list_display = ('batch_code', 'farmer', 'quality_class', 'status', 'created_at')

    list_filter = ('status', 'quality_class', 'created_at')
    search_fields = ('batch_code', 'farmer__username')

    fieldsets = (
        ('Идентификация (Output ID)', {
            'fields': ('batch_code', 'farmer', 'status')
        }),
        ('Результат анализа (Target)', {
            'fields': ('quality_class',)
        }),
        ('Параметры HVI', {
            'fields': (
                ('micronaire', 'strength', 'length', 'uniformity'),
                ('trash_grade', 'trash_cnt', 'trash_area'),
                ('sfi', 'sci', 'color_grade')
            )
        }),
        ('Файлы', {
            'fields': ('cotton_image', 'hvi_file')
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'last_temp', 'is_active')


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('machine', 'timestamp', 'is_prediction', 'probability_failure')