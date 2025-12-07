from django.db import models
from django.conf import settings
import uuid


class CottonBatch(models.Model):
    STATUS_CHOICES = (
        ('RECEIVED', 'Принято'),
        ('ANALYZED', 'Проанализировано'),
        ('EXPORT_READY', 'Готово к экспорту'),
    )

    # --- 1. ИДЕНТИФИКАЦИЯ ---
    batch_code = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Код партии")
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Фермер")

    # [NEW] Регион важен для рекомендации семян (Seed Recommendation)
    region = models.CharField(max_length=100, default="South", verbose_name="Регион выращивания")
    seed_variety = models.CharField(max_length=100, null=True, blank=True, verbose_name="Сорт семян")
    weight_kg = models.FloatField(default=0, verbose_name="Вес партии (кг)")
    seed_recommendations = models.JSONField(null=True, blank=True, verbose_name="Топ-3 Семена (AI)")
    # Файлы
    cotton_image = models.ImageField(upload_to='cotton_images/', null=True, blank=True, verbose_name="Фото образца")
    hvi_file = models.FileField(upload_to='hvi_docs/', null=True, blank=True, verbose_name="HVI файл")

    # --- 2. HVI ПОКАЗАТЕЛИ (Входные данные для XGBoost) ---
    moisture = models.FloatField(null=True, blank=True, verbose_name="Влажность (%)")
    micronaire = models.FloatField(null=True, blank=True, verbose_name="Micronaire")
    strength = models.FloatField(null=True, blank=True, verbose_name="Strength")
    length = models.FloatField(null=True, blank=True, verbose_name="Length")
    uniformity = models.FloatField(null=True, blank=True, verbose_name="Uniformity")

    trash_grade = models.IntegerField(null=True, blank=True, verbose_name="Trash Grade")
    trash_cnt = models.IntegerField(null=True, blank=True, verbose_name="Trash Count")
    trash_area = models.FloatField(null=True, blank=True, verbose_name="Trash Area")

    sfi = models.FloatField(null=True, blank=True, verbose_name="SFI")
    sci = models.IntegerField(null=True, blank=True, verbose_name="SCI")
    color_grade = models.CharField(max_length=20, null=True, blank=True, verbose_name="Color Grade")

    # --- 3. РЕЗУЛЬТАТЫ ИИ (OUTPUT) ---
    # Результат HVI (XGBoost)
    quality_class = models.CharField(max_length=50, null=True, blank=True, verbose_name="Класс качества (HVI)")

    # [NEW] Результат Computer Vision (TensorFlow)
    cv_status = models.CharField(max_length=50, null=True, blank=True, verbose_name="Чистота (CV)")
    cv_confidence = models.FloatField(null=True, blank=True, verbose_name="Уверенность CV")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.batch_code:
            self.batch_code = f"BAT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch_code} | {self.quality_class}"


class Machine(models.Model):
    name = models.CharField(max_length=100)
    machine_type = models.CharField(
        max_length=50,
        default="Generic",  # Add this
        help_text="Type of machine"
    )
    status = models.CharField(max_length=20, default='operational')
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField(default=0)
    vibration = models.FloatField(default=0)
    humidity = models.FloatField(default=0)
    motor_load = models.FloatField(default=0)

    def __str__(self):
        return self.name


class MaintenanceLog(models.Model):
    """
    Журнал. Сюда пишет AI, если предсказывает поломку.
    """
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Станок")
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(verbose_name="Описание проблемы")
    temperature = models.FloatField(default=0, verbose_name="Температура (°C)")
    vibration = models.FloatField(default=0, verbose_name="Вибрация")
    # Результат AI
    is_prediction = models.BooleanField(default=False, verbose_name="Это прогноз AI?")
    probability_failure = models.FloatField(default=0, verbose_name="Вероятность поломки (%)")

    def __str__(self):
        return f"LOG: {self.machine.name} - {self.description}"