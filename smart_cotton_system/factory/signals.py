from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import CottonBatch
from .services import classify_hvi_quality, analyze_cotton_image


# 1. HVI АНАЛИЗ (Запускается ДО сохранения)
@receiver(pre_save, sender=CottonBatch)
def run_hvi_analysis(sender, instance, **kwargs):
    # Запускаем, только если заполнены цифры, но еще нет класса качества
    if instance.micronaire and instance.strength:
        print(f"🧪 Запуск HVI анализа для партии {instance.batch_code}...")
        result = classify_hvi_quality(instance)

        if result:
            instance.quality_class = result
            instance.status = 'ANALYZED'
            print(f"✅ Результат HVI: {result}")


# 2. CV АНАЛИЗ (Запускается ПОСЛЕ сохранения, так как нужно фото на диске)
@receiver(post_save, sender=CottonBatch)
def run_cv_analysis(sender, instance, created, **kwargs):
    # Запускаем, если есть фото, но еще нет статуса CV
    if instance.cotton_image and not instance.cv_status:
        print(f"📷 Запуск CV анализа для фото...")

        # Получаем результат от симуляции
        label, conf = analyze_cotton_image(instance.cotton_image.path)

        # Обновляем запись (используем update, чтобы не вызвать сигнал по кругу)
        CottonBatch.objects.filter(pk=instance.pk).update(
            cv_status=label,
            cv_confidence=conf
        )
        print(f"✅ Результат CV: {label}")