from django.db import models
from django.conf import settings

class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, verbose_name="Гос. номер")
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Водитель")
    
    # Статусы лучше вынести в TextChoices (Best Practice)
    class Status(models.TextChoices):
        IDLE = 'IDLE', 'Ожидает'
        MOVING = 'MOVING', 'В пути'
        UNLOADING = 'UNLOADING', 'Разгрузка'
        
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.IDLE, 
        verbose_name="Статус"
    )

    # Цвет маркера для карты (можно хранить в БД)
    marker_color = models.CharField(max_length=7, default="#f97316", verbose_name="Цвет на карте")
    
    # Route optimization fields
    capacity = models.FloatField(default=20.0, verbose_name="Capacity (units)", help_text="Vehicle capacity in units")
    shift_minutes = models.IntegerField(default=480, verbose_name="Shift duration (minutes)", help_text="Working shift duration in minutes")

    def __str__(self):
        return f"{self.plate_number} ({self.driver})"

class Route(models.Model):
    """
    Оптимальный маршрут.
    path_geojson ожидаем в формате:
    {
      "type": "LineString",
      "coordinates": [[lat, lon], [lat, lon], ...] 
    }
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='routes')
    created_at = models.DateTimeField(auto_now_add=True)
    path_geojson = models.JSONField(verbose_name="Координаты пути")
    estimated_time = models.IntegerField(verbose_name="Время в пути (мин)")
    is_active = models.BooleanField(default=True, verbose_name="Активный маршрут")

    def __str__(self):
        return f"Route for {self.vehicle.plate_number} at {self.created_at}"

class GPSLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='gps_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0)

    class Meta:
        ordering = ['-timestamp']


class Field(models.Model):
    """
    Cotton field for route optimization
    """
    name = models.CharField(max_length=100, verbose_name="Field name")
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")
    demand = models.FloatField(default=1.0, verbose_name="Demand (units)", help_text="Amount of cotton to collect")
    service_time_minutes = models.IntegerField(default=15, verbose_name="Service time (minutes)", help_text="Time needed to service this field")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"


class Depot(models.Model):
    """
    Depot/warehouse location for route optimization
    """
    name = models.CharField(max_length=100, verbose_name="Depot name")
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")
    is_default = models.BooleanField(default=False, verbose_name="Default depot")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"
    
    class Meta:
        verbose_name = "Depot"
        verbose_name_plural = "Depots"


class OptimizationJob(models.Model):
    """
    Store route optimization job results
    """
    depot = models.ForeignKey(Depot, on_delete=models.CASCADE, related_name='optimization_jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    request_data = models.JSONField(verbose_name="Request data")
    ors_request = models.JSONField(verbose_name="ORS request payload", null=True, blank=True)
    ors_solution = models.JSONField(verbose_name="ORS solution", null=True, blank=True)
    ai_summary = models.TextField(blank=True, verbose_name="AI Summary", help_text="Gemini AI generated summary")
    status = models.CharField(max_length=20, default='pending', verbose_name="Status")
    error_message = models.TextField(blank=True, verbose_name="Error message")
    
    def __str__(self):
        return f"Optimization job {self.id} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
