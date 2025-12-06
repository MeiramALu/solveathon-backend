from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CottonBatch
from .services import send_image_to_ml_api


@receiver(post_save, sender=CottonBatch)
def analyze_cotton_on_save(sender, instance, created, **kwargs):
    """
    Срабатывает после сохранения партии.
    """
    # Если это новая запись и есть картинка
    if created and instance.cotton_image:

        # 1. Отправляем во внешний сервис
        ml_result = send_image_to_ml_api(instance.cotton_image.path)

        if ml_result:
            # 2. Парсим ответ (структура зависит от вашего ML API!)
            # Пример: API вернуло {"class": "Supreme", "len": 28.5}

            instance.grade = ml_result.get('class', 'Unknown')
            instance.fiber_length = ml_result.get('len', 0)
            instance.trash_content = ml_result.get('trash', 0)

            # 3. Сохраняем ТОЛЬКО обновленные поля (чтобы не зациклить сигнал)
            instance.save(update_fields=['grade', 'fiber_length', 'trash_content'])