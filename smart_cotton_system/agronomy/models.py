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
        return f"{self.field.name} | {self.timestamp.strftime('%H:%M')} | {self.soil_moisture}%"

class SensorReading(models.Model):
    """Extended sensor readings for water management"""
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='water_readings')
    date = models.DateField()
    location_x = models.FloatField(db_index=True)
    location_y = models.FloatField(db_index=True)

    # Sensor data
    soil_humidity = models.FloatField(help_text="Soil humidity percentage")
    soil_temperature = models.FloatField(help_text="Soil temperature in Celsius")

    # Weather data
    rain = models.FloatField(default=0, help_text="Daily rainfall in mm")
    daily_mean_temperature = models.FloatField(help_text="Air temperature in Celsius")

    # Management data
    irrigation_amount = models.FloatField(default=0, help_text="Irrigation in m3/mu")
    days_since_irrigation = models.IntegerField(default=-1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['field', 'date', 'location_x', 'location_y']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['field', 'date']),
            models.Index(fields=['location_x', 'location_y']),
        ]

    def __str__(self):
        return f"Reading for {self.field.name} on {self.date}"


class IrrigationPrediction(models.Model):
    """AI predictions for irrigation needs"""
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='irrigation_predictions')
    date = models.DateField(db_index=True)
    location_x = models.FloatField()
    location_y = models.FloatField()

    # Predictions
    predicted_humidity = models.FloatField(help_text="Predicted soil humidity for tomorrow")
    current_humidity = models.FloatField(help_text="Current soil humidity")

    # Risk assessment
    dry_risk = models.BooleanField(default=False, help_text="Is there a drought risk?")
    risk_level = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='low'
    )

    # Recommendations
    irrigation_action = models.CharField(
        max_length=20,
        choices=[('IRRIGATE', 'Irrigate'), ('SKIP', 'Skip')],
        default='SKIP'
    )
    recommended_irrigation = models.FloatField(help_text="Recommended irrigation amount in m3/mu")

    # Metadata
    is_future = models.BooleanField(default=False, help_text="Is this a future prediction?")
    confidence_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['field', 'date', 'is_future']),
        ]

    def __str__(self):
        return f"Prediction for {self.field.name} on {self.date}"


class IrrigationEvent(models.Model):
    """Record of actual irrigation events"""
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='irrigation_events')
    date = models.DateField()
    amount = models.FloatField(help_text="Amount in m3/mu")

    # Link to prediction if this was AI-recommended
    prediction = models.ForeignKey(
        IrrigationPrediction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actual_events'
    )

    notes = models.TextField(blank=True)
    # Use settings.AUTH_USER_MODEL which references the correct user model
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Irrigation on {self.date}: {self.amount} m³/mu"
        return f"{self.field.name} | {self.timestamp.strftime('%H:%M')} | Влага: {self.soil_moisture}% | Риск: {self.drought_risk}"
