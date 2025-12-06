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