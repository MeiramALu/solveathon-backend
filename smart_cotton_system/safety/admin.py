from django.contrib import admin
from django.utils.html import mark_safe
from .models import SafetyAlert, Worker, WorkerHealthMetrics, Zone


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('worker_id', 'name', 'role', 'heart_rate', 'spo2', 'temp_c', 'last_updated')
    list_filter = ('role',)
    search_fields = ('name', 'worker_id')
    readonly_fields = ('last_updated', 'created_at')


@admin.register(WorkerHealthMetrics)
class WorkerHealthMetricsAdmin(admin.ModelAdmin):
    list_display = ('worker', 'timestamp', 'heart_rate', 'spo2', 'temp_c', 'safety_status', 'zone')
    list_filter = ('zone', 'alert_panic', 'alert_fall', 'alert_fatigue', 'timestamp')
    search_fields = ('worker__name',)
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone_type', 'lat_min', 'lat_max', 'lon_min', 'lon_max')
    list_filter = ('zone_type',)
    search_fields = ('name',)


@admin.register(SafetyAlert)
class SafetyAlertAdmin(admin.ModelAdmin):
    # Колонки в общем списке
    list_display = (
        'image_preview',  # Мини-фото
        'alert_type',
        'location',
        'timestamp',
        'confidence_percent',  # Красивые проценты
        'is_resolved'
    )

    # Фильтры справа
    list_filter = ('alert_type', 'is_resolved', 'timestamp')

    # Поиск
    search_fields = ('location',)

    # Поля, которые нельзя менять (защита данных AI)
    readonly_fields = ('timestamp', 'confidence', 'detection_details', 'image_preview_large')

    # Группировка полей
    fieldsets = (
        ('Ситуация', {
            'fields': ('alert_type', 'location', 'timestamp', 'is_resolved')
        }),
        ('Фото-доказательство', {
            'fields': ('snapshot', 'image_preview_large')
        }),
        ('Данные нейросети', {
            'fields': ('confidence', 'detection_details'),
            'classes': ('collapse',)  # Можно свернуть этот блок, чтобы не мешал
        }),
    )

    # --- Метод для списка (Маленькое фото) ---
    def image_preview(self, obj):
        if obj.snapshot:
            try:
                return mark_safe(
                    f'<img src="{obj.snapshot.url}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />')
            except Exception:
                return "Ошибка файла"
        return "Нет фото"

    image_preview.short_description = "Снимок"

    # --- Метод для карточки (Большое фото) ---
    def image_preview_large(self, obj):
        if obj.snapshot:
            try:
                return mark_safe(
                    f'<img src="{obj.snapshot.url}" style="max-height: 400px; max-width: 100%; border: 1px solid #ccc;" />')
            except Exception:
                return "Файл не найден"
        return "Нет фото"

    image_preview_large.short_description = "Предпросмотр"

    # --- Метод для красивого отображения процентов ---
    def confidence_percent(self, obj):
        if obj.confidence:
            return f"{int(obj.confidence * 100)}%"
        return "-"

    confidence_percent.short_description = "Точность"