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


# --- МОДУЛЬ 1: Вода (Water) ---
class Field(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название поля")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    polygon_data = models.JSONField(verbose_name="GeoJSON полигона", null=True, blank=True)
    seed_variety = models.ForeignKey(SeedVariety, on_delete=models.SET_NULL, null=True)
    irrigation_active = models.BooleanField(default=False, verbose_name="Полив включен")

    def __str__(self):
        return f"{self.name} ({self.owner})"


class SensorLog(models.Model):
    """
    Лог данных с датчиков.
    """
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)

    # Входные данные (как в Excel)
    soil_moisture = models.FloatField(verbose_name="Влажность (%)")  # Moisture (%) из вашего файла
    weather_temp = models.FloatField(null=True, blank=True, verbose_name="Температура воздуха (°C)")

    # Результат анализа AI (заполняется автоматически)
    irrigation_needed = models.BooleanField(default=False, verbose_name="Нужен полив?")
    ml_message = models.CharField(max_length=255, blank=True, verbose_name="Вердикт AI")

    def __str__(self):
        return f"{self.field.name} | {self.timestamp.strftime('%H:%M')} | {self.soil_moisture}%"