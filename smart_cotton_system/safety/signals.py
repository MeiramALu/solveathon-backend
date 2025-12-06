from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SafetyAlert
from .services import check_fire_with_roboflow


@receiver(post_save, sender=SafetyAlert)
def auto_detect_fire(sender, instance, created, **kwargs):
    # Запускаем только если это новая запись и есть картинка
    if created and instance.snapshot:
        print(f"🔥 Safety AI: Отправляем фото в Roboflow...")

        # 1. Отправляем в API
        predictions = check_fire_with_roboflow(instance.snapshot.path)

        if predictions:
            # Берем самое уверенное предсказание (первое или с макс. confidence)
            best_pred = max(predictions, key=lambda x: x['confidence'])

            # 2. Обновляем данные в базе
            instance.confidence = best_pred['confidence']
            instance.detection_details = best_pred  # Сохраняем x, y, width, height

            # 3. Определяем тип угрозы по классу из Roboflow
            ml_class = best_pred['class']  # Например "Fire-Smoke"

            if "Fire" in ml_class or "Smoke" in ml_class:
                instance.alert_type = 'FIRE'
            elif "Helmet" in ml_class:  # Если у вас модель умеет искать каски
                instance.alert_type = 'NO_HELMET'
            else:
                instance.alert_type = 'DANGER_ZONE'

            # Сохраняем (update_fields важно, чтобы не зациклить)
            instance.save(update_fields=['alert_type', 'confidence', 'detection_details'])
            print(f"✅ Угроза обнаружена: {instance.alert_type} ({instance.confidence:.2f})")