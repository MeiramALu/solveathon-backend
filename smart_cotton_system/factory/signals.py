from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import CottonBatch
from .services import classify_cotton_quality  # <-- ИСПРАВЛЕННЫЙ ИМПОРТ


@receiver(pre_save, sender=CottonBatch)
def run_quality_analysis(sender, instance, **kwargs):
    """
    Автоматически вычисляет класс хлопка перед сохранением,
    если введены показатели HVI.
    """
    # Если введены ключевые показатели, запускаем расчет
    if instance.micronaire and instance.strength:

        predicted_class = classify_cotton_quality(instance)

        if predicted_class:
            instance.quality_class = predicted_class
            instance.status = 'ANALYZED'
            print(f"🤖 AI Analysis: Партия {instance.batch_code} -> {predicted_class}")