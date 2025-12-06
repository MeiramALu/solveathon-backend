import requests
from django.conf import settings


def analyze_safety_snapshot(image_path):
    """
    Отправляет снапшот на ML для детекции угроз (Огонь, Каска и т.д.)
    """
    url = f"{settings.ML_API_URL}/safety-check"  # Предполагаемый эндпоинт
    headers = {"Authorization": f"Bearer {settings.ML_API_KEY}"}

    try:
        with open(image_path, 'rb') as img_file:
            response = requests.post(url, headers=headers, files={'file': img_file}, timeout=5)

        if response.status_code == 200:
            return response.json()  # Ожидаем: {"alert_type": "FIRE", "confidence": 0.98}
    except Exception as e:
        print(f"Safety ML Error: {e}")

    return None