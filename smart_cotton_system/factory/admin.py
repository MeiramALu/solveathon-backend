from django.contrib import admin
from .models import CottonBatch, Machine, MaintenanceLog


@admin.register(CottonBatch)
class CottonBatchAdmin(admin.ModelAdmin):
    # В списке теперь видно: Качество HVI, Чистоту CV и Регион
    list_display = ('batch_code', 'farmer', 'quality_class', 'cv_status', 'region', 'status')

    # Фильтры: можно найти весь "Грязный" хлопок или хлопок с "Юга"
    list_filter = ('status', 'quality_class', 'cv_status', 'region', 'created_at')

    search_fields = ('batch_code', 'farmer__username')

    # Защищаем поля AI от ручного редактирования (чтобы видели, но не меняли)
    readonly_fields = ('quality_class', 'cv_status', 'cv_confidence', 'created_at')

    fieldsets = (
        ('Идентификация', {
            'fields': ('batch_code', 'farmer', 'status', 'created_at')
        }),
        ('Агрономия (Для подбора семян)', {
            # Важные поля для 3-го пункта ТЗ
            'fields': ('region', 'seed_variety', 'weight_kg')
        }),
        ('Результаты AI анализа (Вычисляются автоматически)', {
            # Сюда пишут результаты HVI и CV
            'fields': ('quality_class', 'cv_status', 'cv_confidence')
        }),
        ('Параметры HVI (Входные данные)', {
            'fields': (
                ('moisture', 'micronaire', 'strength'),  # Добавили влажность
                ('length', 'uniformity'),
                ('trash_grade', 'trash_cnt', 'trash_area'),
                ('sfi', 'sci', 'color_grade')
            )
        }),
        ('Файлы', {
            'fields': ('cotton_image', 'hvi_file')
        }),
    )


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    # Добавили вибрацию и нагрузку в список, чтобы сразу видеть перегрев
    list_display = ('name', 'status', 'last_temp', 'last_vibration', 'last_motor_load', 'updated_at')
    list_filter = ('status', 'is_active')
    search_fields = ('name',)


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('machine', 'timestamp', 'is_prediction', 'probability_failure')
    list_filter = ('is_prediction', 'machine')
    readonly_fields = ('timestamp',)