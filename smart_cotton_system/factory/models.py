from django.db import models
from django.conf import settings
import uuid


class CottonBatch(models.Model):
    STATUS_CHOICES = (
        ('RECEIVED', 'Принято'),
        ('ANALYZED', 'Проанализировано'),
        ('EXPORT_READY', 'Готово к экспорту'),
    )

    # --- 1. ИДЕНТИФИКАЦИЯ (IDENTIFICATION) ---
    batch_code = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Код партии (ID)")
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Фермер")
    seed_variety = models.CharField(max_length=100, null=True, blank=True, verbose_name="Сорт семян")
    cotton_image = models.ImageField(upload_to='cotton_images/', null=True, blank=True, verbose_name="Фото образца")
    hvi_file = models.FileField(upload_to='hvi_docs/', null=True, blank=True, verbose_name="HVI файл")
    weight_kg = models.FloatField(default=0, verbose_name="Вес партии (кг)")
    # --- 2. HVI ПОКАЗАТЕЛИ (INPUT DATA) ---
    # Зрелость и прочность
    moisture = models.FloatField(null=True, blank=True, verbose_name="Влажность (%)")
    micronaire = models.FloatField(null=True, blank=True, verbose_name="Micronaire (3.5–4.9)")
    strength = models.FloatField(null=True, blank=True, verbose_name="Strength (г/текс)")

    # Длина и равномерность
    length = models.FloatField(null=True, blank=True, verbose_name="Length (дюймы)")
    uniformity = models.FloatField(null=True, blank=True, verbose_name="Uniformity (%)")

    # Засоренность (Trash)
    trash_grade = models.IntegerField(null=True, blank=True, verbose_name="Trash Grade (1-7)")
    trash_cnt = models.IntegerField(null=True, blank=True, verbose_name="Trash Count (шт)")
    trash_area = models.FloatField(null=True, blank=True, verbose_name="Trash Area (%)")

    # Индексы (SFI, SCI)
    sfi = models.FloatField(null=True, blank=True, verbose_name="Short Fiber Index (SFI)")
    sci = models.IntegerField(null=True, blank=True, verbose_name="Spinning Consistency Index (SCI)")

    # Цвет
    color_grade = models.CharField(max_length=20, null=True, blank=True, verbose_name="Color Grade (напр. 31-1)")

    # --- 3. РЕЗУЛЬТАТ (OUTPUT) ---
    # Это целевая переменная, которую определяет ML или Лаборант
    quality_class = models.CharField(max_length=50, null=True, blank=True, verbose_name="★ Quality Class (Target)")

    # Системные поля
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def save(self, *args, **kwargs):
        if not self.batch_code:
            self.batch_code = f"BAT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch_code} | Class: {self.quality_class}"


# --- Модели станков (оставляем без изменений) ---
class Machine(models.Model):
    name = models.CharField(max_length=100, verbose_name="ID Станка (GIN-01)")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    status = models.CharField(max_length=20, default='OK', verbose_name="Статус")

    # Телеметрия (последние данные с датчиков)
    last_temp = models.FloatField(default=0, verbose_name="Температура (°C)")
    last_vibration = models.FloatField(default=0, verbose_name="Вибрация")
    # Новые поля из Excel
    last_motor_load = models.FloatField(default=0, verbose_name="Нагрузка мотора (%)")
    last_humidity = models.FloatField(default=0, verbose_name="Влажность в цеху (%)")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")

    def __str__(self):
        return f"{self.name} | {self.status}"


class MaintenanceLog(models.Model):
    """
    Журнал. Сюда пишет AI, если предсказывает поломку.
    """
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Станок")
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(verbose_name="Описание проблемы")

    # Результат AI
    is_prediction = models.BooleanField(default=False, verbose_name="Это прогноз AI?")
    probability_failure = models.FloatField(default=0, verbose_name="Вероятность поломки (%)")

    def __str__(self):
        return f"LOG: {self.machine.name} - {self.description}"