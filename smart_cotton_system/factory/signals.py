from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import CottonBatch
# Не забудьте импортировать функцию рекомендаций!
from .services import classify_hvi_quality, analyze_cotton_image, get_seed_recommendations


@receiver(pre_save, sender=CottonBatch)
def run_ai_analysis(sender, instance, **kwargs):
    # 1. HVI АНАЛИЗ
    if instance.micronaire and instance.strength:
        result = classify_hvi_quality(instance)
        if result:
            instance.quality_class = result
            instance.status = 'ANALYZED'

    # 2. ПОДБОР СЕМЯН (Новое!)
    # Если указан регион, но еще нет рекомендаций
    if instance.region and not instance.seed_recommendations:
        print(f"🌱 Подбор семян для региона {instance.region}...")
        recommendations = get_seed_recommendations(instance.region)
        instance.seed_recommendations = recommendations


@receiver(post_save, sender=CottonBatch)
def run_cv_analysis(sender, instance, created, **kwargs):
    # 3. CV АНАЛИЗ (Фото)
    if instance.cotton_image and not instance.cv_status:
        label, conf = analyze_cotton_image(instance.cotton_image.path)
        CottonBatch.objects.filter(pk=instance.pk).update(
            cv_status=label,
            cv_confidence=conf
        )