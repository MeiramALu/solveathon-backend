from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SensorLog
from .services import predict_irrigation_need


@receiver(post_save, sender=SensorLog)
def check_soil_status(sender, instance, created, **kwargs):
    if created:
        print(f"💧 Water AI: Анализ влажности {instance.soil_moisture}%...")

        should_irrigate = predict_irrigation_need(instance.soil_moisture, instance.weather_temp)

        if should_irrigate:
            instance.irrigation_needed = True
            instance.save(update_fields=['irrigation_needed'])
            print(f"⚠️ РЕКОМЕНДАЦИЯ: Включить полив на поле {instance.field.name}!")