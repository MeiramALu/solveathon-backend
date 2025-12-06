import requests
from django.conf import settings


def predict_irrigation_need(moisture, temp):
    """
    Отправляет данные почвы и погоды в ML
    """
    url = f"{settings.ML_API_URL}/water-predict"
    # ... стандартный код запроса requests.post ...
    # Для простоты вернем локальную логику, как в прошлом примере,
    # или раскомментируйте requests для реального ML.

    # Локальная ML-логика (Rule-based AI)
    if moisture < 30:
        return True
    if temp and temp > 35 and moisture < 40:
        return True
    return False