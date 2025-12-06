from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SafetyAlert
from .services import analyze_safety_snapshot


@receiver(post_save, sender=SafetyAlert)
def auto_detect_danger(sender, instance, created, **kwargs):
    # Запускаем только если запись новая и есть картинка
    if created and instance.snapshot:
        print(f"🚨 Safety AI: Анализ снимка для {instance.location}...")

        result = analyze_safety_snapshot(instance.snapshot.path)

        if result:
            # Обновляем тип угрозы на основе ответа ИИ
            instance.alert_type = result.get('alert_type', 'DANGER_ZONE')
            # Если ИИ уверен, что угрозы нет, ставим resolved (пример логики)
            if result.get('safe', False):
                instance.is_resolved = True

            instance.save(update_fields=['alert_type', 'is_resolved'])
            print(f"✅ Угроза определена: {instance.alert_type}")