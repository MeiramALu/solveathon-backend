from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Route


# Здесь используем простую заглушку сервиса, так как в модели Route
# у нас нет полей "откуда" и "куда", мы их подразумеваем.
# Для примера будем генерировать маршрут при создании записи.

@receiver(post_save, sender=Route)
def calculate_route_ai(sender, instance, created, **kwargs):
    if created and not instance.path_geojson:
        print(f"🚚 Logistics AI: Построение маршрута для ТС {instance.vehicle}...")

        # В реальности мы бы брали координаты из задачи на перевозку
        # Здесь для примера имитируем вызов
        # result = build_optimal_route(instance.vehicle.id, [76.9, 43.2], [76.95, 43.25])

        # ЗАГЛУШКА (пока нет реального API)
        import random
        result = {
            "path_geojson": {
                "type": "LineString",
                "coordinates": [[76.9, 43.2], [76.92, 43.22], [76.95, 43.25]]
            },
            "estimated_time": random.randint(20, 120)
        }

        if result:
            instance.path_geojson = result['path_geojson']
            instance.estimated_time = result['estimated_time']
            instance.save(update_fields=['path_geojson', 'estimated_time'])
            print("✅ Маршрут построен")