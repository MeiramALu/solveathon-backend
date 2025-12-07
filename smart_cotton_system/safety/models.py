from django.db import models


class SafetyAlert(models.Model):
    ALERT_TYPES = (
        ('FIRE', 'Пожар'),
        ('SMOKE', 'Дым'),
        ('NO_HELMET', 'Нет каски'),
        ('DANGER_ZONE', 'Человек в опасной зоне'),
    )

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, verbose_name="Тип угрозы")
    location = models.CharField(max_length=100, verbose_name="Камера/Зона")
    timestamp = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    confidence = models.FloatField(null=True, blank=True, verbose_name="Точность AI")
    detection_details = models.JSONField(null=True, blank=True,
                                         verbose_name="Детали (bbox)")
    snapshot = models.ImageField(upload_to='safety_alerts/', null=True, blank=True)

    def __str__(self):
        return f"ALARM: {self.alert_type} ({self.confidence or 0:.2f})"



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

    # --- Новые данные с датчиков ---
    heart_rate = models.FloatField(verbose_name="Пульс (уд/мин)")
    spo2 = models.IntegerField(verbose_name="Кислород SpO2 (%)")
    body_temp = models.FloatField(verbose_name="Температура (°C)")
    stress_index = models.FloatField(verbose_name="Уровень стресса")
    noise_level = models.FloatField(verbose_name="Уровень шума (дБ)")
    steps = models.IntegerField(default=0, verbose_name="Шаги")
    sleep_quality = models.IntegerField(default=0, verbose_name="Качество сна (%)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OK', verbose_name="Статус здоровья")

    def save(self, *args, **kwargs):
        """
        AI-анализ показателей перед сохранением.
        Определяет статус на основе медицинских норм и охраны труда.
        """
        self.status = 'OK'  # Сбрасываем статус

        # 1. Проверка Сердца (Брадикардия < 40 или Тахикардия > 140)
        if self.heart_rate > 140 or self.heart_rate < 40:
            self.status = 'CRITICAL_PULSE'

        # 2. Проверка Кислорода (Норма 95-100%, ниже 90% - гипоксия)
        elif self.spo2 < 90:
            self.status = 'HYPOXIA'

        # 3. Проверка Температуры (Выше 38 - жар)
        elif self.body_temp > 38.0:
            self.status = 'FEVER'

        # 4. Проверка Шума (Выше 85 дБ опасно для длительной работы)
        elif self.noise_level > 85.0:
            self.status = 'DANGEROUS_NOISE'

        # 5. Проверка Стресса (Если шкала 0-100, то выше 80 - это выгорание)
        elif self.stress_index > 80.0:
            self.status = 'HIGH_STRESS'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Worker {self.worker_id} | {self.status} | HR: {self.heart_rate} | SpO2: {self.spo2}%"