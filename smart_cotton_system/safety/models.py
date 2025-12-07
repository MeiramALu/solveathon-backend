from django.db import models


# --- ВНИМАНИЕ: Здесь НЕ должно быть строки "from .models import SafetyAlert" ---

class SafetyAlert(models.Model):
    ALERT_TYPES = (
        ('FIRE', '🔥 Пожар'),
        ('SMOKE', '💨 Дым'),
        ('NO_HELMET', '👷 Нет каски'),
        ('DANGER_ZONE', '⚠️ Опасная зона'),
    )

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name="Тип угрозы")
    location = models.CharField(max_length=100, verbose_name="Камера/Зона")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время обнаружения")
    is_resolved = models.BooleanField(default=False, verbose_name="Проблема решена?")

    # Технические данные от AI
    confidence = models.FloatField(null=True, blank=True, verbose_name="Точность AI (0.0-1.0)")
    detection_details = models.JSONField(null=True, blank=True, verbose_name="Детали (координаты bbox)")
    snapshot = models.ImageField(upload_to='safety_alerts/', null=True, blank=True, verbose_name="Снимок с камеры")

    class Meta:
        verbose_name = "Тревожный сигнал (AI)"
        verbose_name_plural = "Тревожные сигналы (AI)"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_alert_type_display()} | {self.location}"


class WorkerHealthLog(models.Model):
    STATUS_CHOICES = (
        ('OK', 'Норма'),
        ('CRITICAL_PULSE', 'Критический пульс'),
        ('FEVER', 'Жар/Лихорадка'),
        ('HYPOXIA', 'Гипоксия (мало кислорода)'),
        ('HIGH_STRESS', 'Высокий стресс'),
        ('DANGEROUS_NOISE', 'Опасный уровень шума'),
    )

    worker_id = models.CharField(max_length=50, verbose_name="ID Сотрудника")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время замера")

    # Данные с датчиков
    heart_rate = models.FloatField(verbose_name="Пульс (уд/мин)")
    spo2 = models.IntegerField(verbose_name="Кислород SpO2 (%)")
    body_temp = models.FloatField(verbose_name="Температура (°C)")
    stress_index = models.FloatField(verbose_name="Уровень стресса")
    noise_level = models.FloatField(verbose_name="Уровень шума (дБ)")
    steps = models.IntegerField(default=0, verbose_name="Шаги")
    sleep_quality = models.IntegerField(default=0, verbose_name="Качество сна (%)")

    # Итоговый статус
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OK', verbose_name="Статус здоровья")

    def save(self, *args, **kwargs):
        self.status = 'OK'

        if self.heart_rate > 140 or self.heart_rate < 40:
            self.status = 'CRITICAL_PULSE'
        elif self.spo2 < 90:
            self.status = 'HYPOXIA'
        elif self.body_temp > 38.0:
            self.status = 'FEVER'
        elif self.noise_level > 85.0:
            self.status = 'DANGEROUS_NOISE'
        elif self.stress_index > 80.0:
            self.status = 'HIGH_STRESS'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Worker {self.worker_id} | {self.status}"