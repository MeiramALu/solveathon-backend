from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import SafetyAlert
from .services import check_with_roboflow
import threading


@receiver(post_save, sender=SafetyAlert)
def auto_detect_threats(sender, instance, created, **kwargs):
    if created and instance.snapshot:
        print(f"🚀 Старт анализа (ID: {instance.id})")
        thread = threading.Thread(target=process_image, args=(instance,))
        thread.start()


def process_image(instance):
    try:
        image_path = instance.snapshot.path

        # --- ШАГ 1: ПОЖАР (Fire) ---
        print("🔥 Проверка модели пожара...")
        fire_preds = check_with_roboflow(
            image_path,
            settings.ROBOFLOW_FIRE_MODEL_ID,
            settings.ROBOFLOW_FIRE_VERSION
        )

        # --- ШАГ 2: КАСКИ (PPE) ---
        print("👷 Проверка модели касок...")
        ppe_preds = check_with_roboflow(
            image_path,
            settings.ROBOFLOW_PPE_MODEL_ID,
            settings.ROBOFLOW_PPE_VERSION
        )

        # --- ШАГ 3: АНАЛИЗ УГРОЗ ---
        all_threats = []

        # 3.1 Пожар
        if fire_preds:
            fire_objects = [p for p in fire_preds if p['confidence'] >= 0.4]
            if fire_objects:
                best_fire = max(fire_objects, key=lambda x: x['confidence'])
                best_fire['custom_type'] = 'FIRE'
                all_threats.append(best_fire)

        # 3.2 Каски (УЛУЧШЕННАЯ ЛОГИКА)
        if ppe_preds:
            # Собираем, что мы нашли
            found_helmet = False
            found_vest = False
            best_vest_pred = None

            # Есть ли явные классы "NO-Helmet"?
            explicit_violations = []

            for p in ppe_preds:
                cls = p['class'].upper()
                conf = p['confidence']

                # Запоминаем, что нашли
                if 'HELMET' in cls and 'NO' not in cls:
                    found_helmet = True

                if 'VEST' in cls and 'NO' not in cls:
                    found_vest = True
                    if not best_vest_pred or conf > best_vest_pred['confidence']:
                        best_vest_pred = p  # Запоминаем жилет как "улику"

                # Если модель умеет искать NO-HELMET
                if conf >= 0.20 and ('NO' in cls or 'MISSING' in cls or 'HEAD' in cls):
                    explicit_violations.append(p)

            # СЦЕНАРИЙ А: Модель нашла явное "Нет каски" или "Голова"
            if explicit_violations:
                best_violation = max(explicit_violations, key=lambda x: x['confidence'])
                best_violation['custom_type'] = 'NO_HELMET'
                all_threats.append(best_violation)

            # СЦЕНАРИЙ Б (ДЕДУКЦИЯ): Есть Жилет, но НЕТ Каски -> Нарушение!
            elif found_vest and not found_helmet:
                print("   ⚠️ ЛОГИКА: Найден человек в жилете, но без каски!")
                # Используем найденный жилет как координаты нарушения
                violation_obj = best_vest_pred.copy()
                violation_obj['custom_type'] = 'NO_HELMET'
                violation_obj['confidence'] = 0.99  # Мы уверены, так как это логический вывод
                all_threats.append(violation_obj)

        # --- ШАГ 4: РЕШЕНИЕ ---
        if all_threats:
            winner = max(all_threats, key=lambda x: x['confidence'])
            update_alert(instance, winner['custom_type'], winner)
        else:
            print(f"✅ Угроз не обнаружено.")

    except Exception as e:
        print(f"❌ Ошибка в анализе: {e}")


def update_alert(instance, alert_type, prediction):
    instance.alert_type = alert_type
    instance.confidence = prediction['confidence']
    if 'custom_type' in prediction:
        del prediction['custom_type']
    instance.detection_details = prediction
    instance.save(update_fields=['alert_type', 'confidence', 'detection_details'])
    print(f"💾 ЗАПИСАНО В БД: {alert_type}")