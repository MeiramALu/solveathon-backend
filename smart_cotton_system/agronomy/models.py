from django.db import models
from django.conf import settings


# --- МОДУЛЬ 7: Селекция (Seeds) ---
class SeedVariety(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    recommended_soil = models.CharField(max_length=100)
    expected_yield = models.FloatField(help_text="Ожидаемый урожай ц/га")


# --- МОДУЛЬ 1: Вода (Water) ---
class Field(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    polygon_data = models.JSONField(verbose_name="GeoJSON полигона", null=True, blank=True)  # Для карты Leaflet
    seed_variety = models.ForeignKey(SeedVariety, on_delete=models.SET_NULL, null=True)

    # Статус полива
    irrigation_active = models.BooleanField(default=False)


class SensorLog(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    soil_moisture = models.FloatField()
    weather_temp = models.FloatField(null=True)  # Данные с OpenWeather