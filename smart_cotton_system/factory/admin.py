from django.contrib import admin
from django.utils.html import mark_safe
from .models import CottonBatch, Machine, MaintenanceLog


@admin.register(CottonBatch)
class CottonBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_code', 'farmer', 'quality_class', 'cv_status', 'region')
    list_filter = ('status', 'quality_class', 'region')
    search_fields = ('batch_code',)

    readonly_fields = ('quality_class', 'cv_status', 'cv_confidence', 'created_at', 'show_seeds')

    fieldsets = (
        ('Идентификация', {
            'fields': ('batch_code', 'farmer', 'status', 'created_at')
        }),
        ('Агрономия (Входные данные)', {
            'fields': ('region', 'seed_variety', 'weight_kg')
        }),
        ('🌱 Рекомендации AI (Семена)', {
            'fields': ('show_seeds',)
        }),
        ('📊 Результаты анализа (HVI + CV)', {
            'fields': ('quality_class', 'cv_status', 'cv_confidence')
        }),
        ('Параметры HVI', {
            'fields': (
                ('micronaire', 'strength', 'length'),
                ('trash_grade', 'trash_cnt', 'color_grade')
            )
        }),
        ('Файлы', {
            'fields': ('cotton_image', 'hvi_file')
        }),
    )

    def show_seeds(self, obj):
        if not obj.seed_recommendations:
            return "Нет данных (Укажите регион и сохраните)"

        html = "<ul style='margin-left: 0; padding-left: 15px;'>"
        for i, rec in enumerate(obj.seed_recommendations):
            icon = "🏆" if i == 0 else "🥈" if i == 1 else "🥉"
            html += f"<li>{icon} <b>{rec['variety']}</b> — Прогноз: {rec['predicted_yield']} кг/га</li>"
        html += "</ul>"
        return mark_safe(html)

    show_seeds.short_description = "Топ-3 Сорта для региона"


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'last_temp', 'last_vibration', 'last_motor_load', 'updated_at')
    list_filter = ('status', 'is_active')
    search_fields = ('name',)


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    # --- ВАЖНОЕ ОБНОВЛЕНИЕ ЗДЕСЬ ---
    # Добавили temperature и vibration, чтобы видеть историю для графиков
    list_display = (
        'machine',
        'timestamp',
        'temperature',  # <--- Новое
        'vibration',  # <--- Новое
        'probability_failure',
        'is_prediction'
    )

    list_filter = ('is_prediction', 'machine', 'timestamp')

    # Делаем поля доступными только для чтения (историю нельзя менять)
    readonly_fields = ('timestamp', 'temperature', 'vibration', 'probability_failure', 'is_prediction')