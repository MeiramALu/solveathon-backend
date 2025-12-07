from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


# --- ВНИМАНИЕ: Здесь НЕ должно быть строки "from .models import SafetyAlert" ---

class Worker(models.Model):
    """Worker entity for safety monitoring"""
    worker_id = models.IntegerField(unique=True, verbose_name="Worker ID")
    name = models.CharField(max_length=100, verbose_name="Full Name")
    role = models.CharField(max_length=100, verbose_name="Role/Position")
    
    # Current location
    latitude = models.FloatField(default=0.0, verbose_name="Latitude")
    longitude = models.FloatField(default=0.0, verbose_name="Longitude")
    altitude = models.FloatField(default=0.0, verbose_name="Altitude (m)")
    
    # Current vitals
    heart_rate = models.FloatField(default=75.0, verbose_name="Heart Rate (BPM)")
    steps = models.IntegerField(default=0, verbose_name="Steps Count")
    activity_level = models.IntegerField(default=0, verbose_name="Activity Level (0-10)")
    temp_c = models.FloatField(default=36.6, verbose_name="Body Temperature (°C)")
    spo2 = models.IntegerField(default=98, verbose_name="Blood Oxygen (%)")
    noise_level = models.FloatField(default=60.0, verbose_name="Ambient Noise (dB)")
    hrv = models.FloatField(default=50.0, verbose_name="Heart Rate Variability (ms)")
    sleep_score = models.IntegerField(default=80, verbose_name="Sleep Score (0-100)")
    
    # Meta
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Worker"
        verbose_name_plural = "Workers"
        ordering = ['worker_id']
    
    def __str__(self):
        return f"{self.name} (ID: {self.worker_id})"


class Zone(models.Model):
    """Hazardous zones in the facility"""
    ZONE_TYPES = (
        ('CHEMICAL', 'Chemical Storage'),
        ('ASSEMBLY', 'Assembly Line'),
        ('LOADING', 'Loading Dock'),
        ('SAFE', 'Safe Zone'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Zone Name")
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES, default='SAFE')
    
    # Bounding box coordinates (percentage 0-100)
    lat_min = models.FloatField(verbose_name="Latitude Min")
    lat_max = models.FloatField(verbose_name="Latitude Max")
    lon_min = models.FloatField(verbose_name="Longitude Min")
    lon_max = models.FloatField(verbose_name="Longitude Max")
    
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Zone"
        verbose_name_plural = "Zones"
    
    def __str__(self):
        return f"{self.name} ({self.get_zone_type_display()})"
    
    def contains_point(self, lat, lon):
        """Check if a point is within this zone"""
        return (self.lat_min <= lat <= self.lat_max and 
                self.lon_min <= lon <= self.lon_max)


class WorkerHealthMetrics(models.Model):
    """Time-series health metrics for workers"""
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='health_logs')
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Vitals snapshot
    heart_rate = models.FloatField(verbose_name="Heart Rate (BPM)")
    spo2 = models.IntegerField(verbose_name="Blood Oxygen (%)")
    temp_c = models.FloatField(verbose_name="Body Temperature (°C)")
    hrv = models.FloatField(verbose_name="HRV (ms)")
    steps = models.IntegerField(verbose_name="Steps")
    activity_level = models.IntegerField(verbose_name="Activity Level")
    noise_level = models.FloatField(verbose_name="Noise Level (dB)")
    
    # Location
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    
    # Alerts
    alert_panic = models.BooleanField(default=False)
    alert_fall = models.BooleanField(default=False)
    alert_fatigue = models.BooleanField(default=False)
    alert_environment = models.BooleanField(default=False)
    alert_acoustic = models.BooleanField(default=False)
    alert_geofence = models.BooleanField(default=False)
    
    safety_status = models.CharField(max_length=500, default="OK")
    zone = models.CharField(max_length=100, default="Safe Zone")
    
    class Meta:
        verbose_name = "Health Metric"
        verbose_name_plural = "Health Metrics"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['worker', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.worker.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


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