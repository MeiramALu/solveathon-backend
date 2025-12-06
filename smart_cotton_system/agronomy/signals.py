from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import SensorLog
from .services import analyze_water_needs


@receiver(pre_save, sender=SensorLog)
def run_water_ai(sender, instance, **kwargs):
    """
    Перед сохранением записи запускаем анализ.
    """
    # Вызываем нашу функцию
    need_water, message = analyze_water_needs(instance.soil_moisture, instance.weather_temp)

    # Записываем результат в базу
    instance.irrigation_needed = need_water
    instance.ml_message = message