from django.db import models

class SafetyAlert(models.Model):
    ALERT_TYPES = (
        ('FIRE', 'Пожар'),
        ('SMOKE', 'Дым'),
        ('NO_HELMET', 'Нет каски'),
        ('DANGER_ZONE', 'Человек в опасной зоне'),
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    location = models.CharField(max_length=100) # Название зоны/камеры
    timestamp = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    snapshot = models.ImageField(upload_to='safety_alerts/', null=True) # Скриншот с камеры

    def __str__(self):
        return f"ALARM: {self.alert_type} at {self.location}"
