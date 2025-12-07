from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import SafetyAlert
from .services import check_with_roboflow


@receiver(post_save, sender=SafetyAlert)
def auto_detect_threats(sender, instance, created, **kwargs):
    # Запускаем только если создана новая запись со снимком
    if created and instance.snapshot:
        print(f"🔍 Safety AI: Начинаем анализ изображения...")

        # --- ЭТАП 1: Проверка на ПОЖАР (Приоритет) ---
        fire_preds = check_with_roboflow(
            instance.snapshot.path,
            settings.ROBOFLOW_FIRE_MODEL_ID,
            settings.ROBOFLOW_FIRE_VERSION
        )

        best_pred = None

        # Ищем огонь или дым
        if fire_preds:
            fire_threat = max(fire_preds, key=lambda x: x['confidence'])
            if fire_threat['confidence'] > 0.4:
                best_pred = fire_threat
                instance.alert_type = 'FIRE'

        # --- ЭТАП 2: Если пожара нет, проверяем КАСКИ (PPE) ---
        if not best_pred:
            ppe_preds = check_with_roboflow(
                instance.snapshot.path,
                settings.ROBOFLOW_PPE_MODEL_ID,
                settings.ROBOFLOW_PPE_VERSION
            )

            # В этой модели классы обычно: 'NO-Helmet', 'NO-Vest', 'Helmet', 'Vest'
            # Нас интересуют только нарушения (NO-...)
            violations = [p for p in ppe_preds if 'NO' in p['class'].upper()]

            if violations:
                best_pred = max(violations, key=lambda x: x['confidence'])
                instance.alert_type = 'NO_HELMET'

        # --- ЭТАП 3: Сохранение результата ---
        if best_pred:
            instance.confidence = best_pred['confidence']
            instance.detection_details = best_pred

            # Сохраняем (update_fields нужен, чтобы не вызвать сигнал снова)
            instance.save(update_fields=['alert_type', 'confidence', 'detection_details'])
            print(f"✅ УГРОЗА ПОДТВЕРЖДЕНА: {instance.alert_type}")
        else:
            print("✅ Угроз не обнаружено.")