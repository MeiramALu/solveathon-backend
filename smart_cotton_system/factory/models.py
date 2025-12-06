from django.db import models
from django.conf import settings


# --- МОДУЛЬ 2: Контроль качества (Quality Control) ---
class CottonBatch(models.Model):
    batch_code = models.CharField(max_length=50, unique=True)
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Файлы для ML
    cotton_image = models.ImageField(upload_to='cotton_images/', null=True, blank=True, verbose_name="Фото хлопка")
    hvi_file = models.FileField(upload_to='hvi_docs/', null=True, blank=True, verbose_name="HVI CSV/Excel")

    # Результаты анализа (заполняет ML или Лаборант)
    grade = models.CharField(max_length=20, null=True, blank=True, verbose_name="Сорт")
    fiber_length = models.FloatField(null=True, blank=True)
    micr = models.FloatField(null=True, blank=True)
    strength = models.FloatField(null=True, blank=True)
    trash_content = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=20, default='RECEIVED')
    created_at = models.DateTimeField(auto_now_add=True)


# --- МОДУЛЬ 4: Smart Factory ---
class Machine(models.Model):
    """Станки (Джин-машины)"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, default='OK')  # OK, WARNING, CRITICAL

    # Телеметрия (последние данные)
    last_temp = models.FloatField(default=0)
    last_vibration = models.FloatField(default=0)

    def __str__(self):
        return f"{self.name} [{self.status}]"


class MaintenanceLog(models.Model):
    """Журнал ремонтов и предсказаний поломок"""
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    is_prediction = models.BooleanField(default=False, verbose_name="Это прогноз AI?")
    probability_failure = models.FloatField(default=0, verbose_name="Вероятность поломки %")