from django.db import models
from django.conf import settings


class Vehicle(models.Model):
    plate_number = models.CharField(max_length=20, verbose_name="Гос. номер")
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Водитель")
    status = models.CharField(max_length=20, default='IDLE', verbose_name="Статус")
    current_load = models.FloatField(default=0, verbose_name="Текущий вес груза (кг)")
    def __str__(self):
        return self.plate_number


class GPSLog(models.Model):
    """История передвижений (для Live Tracking)"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='gps_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0)

    class Meta:
        ordering = ['-timestamp']


class Route(models.Model):
    """Оптимальный маршрут, построенный AI"""
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    path_geojson = models.JSONField(verbose_name="Координаты пути")
    estimated_time = models.IntegerField(verbose_name="Время в пути (мин)")