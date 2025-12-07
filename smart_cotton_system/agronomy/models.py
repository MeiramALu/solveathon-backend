from django.db import models
from django.conf import settings


# --- МОДУЛЬ 7: Селекция (Seeds) ---
class SeedVariety(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    recommended_soil = models.CharField(max_length=100)
    expected_yield = models.FloatField(help_text="Ожидаемый урожай ц/га")

    def __str__(self):
        return self.name


class SeedVariety(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    recommended_soil = models.CharField(max_length=100)
    expected_yield = models.FloatField(help_text="Ожидаемый урожай ц/га")

    def __str__(self):
        return self.name


class Field(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название поля")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    polygon_data = models.JSONField(verbose_name="GeoJSON полигона", null=True, blank=True)
    seed_variety = models.ForeignKey(SeedVariety, on_delete=models.SET_NULL, null=True)

    irrigation_active = models.BooleanField(default=False, verbose_name="Полив включен (Статус клапана)")
    is_smart_mode = models.BooleanField(default=True, verbose_name="Авто-режим AI")  # Если True, AI сам включает воду

    def __str__(self):
        return f"{self.name} ({self.owner})"


class SensorLog(models.Model):

    RISK_CHOICES = (
        ('LOW', '🟢 Низкий риск'),
        ('MEDIUM', '🟡 Средний риск'),
        ('HIGH', '🔴 Высокий риск засухи'),
    )

    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)

    soil_moisture = models.FloatField(verbose_name="Влажность почвы (%)")
    weather_temp = models.FloatField(null=True, blank=True, verbose_name="Температура воздуха (°C)")
    air_humidity = models.FloatField(null=True, blank=True, verbose_name="Влажность воздуха (%)")  # Важно для засухи
    rain_probability = models.FloatField(default=0, verbose_name="Вероятность дождя (%)")  # Прогноз погоды

    irrigation_needed = models.BooleanField(default=False, verbose_name="Рекомендация: Полив нужен?")
    recommended_water_amount = models.FloatField(default=0, verbose_name="Сколько литров/м²")  # Авто-распределение

    drought_risk = models.CharField(max_length=20, choices=RISK_CHOICES, default='LOW', verbose_name="Риск засухи")
    ml_message = models.CharField(max_length=255, blank=True, verbose_name="Вердикт AI")

    def __str__(self):
        return f"{self.field.name} | {self.timestamp.strftime('%H:%M')} | Влага: {self.soil_moisture}% | Риск: {self.drought_risk}"