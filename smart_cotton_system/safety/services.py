import requests
from django.conf import settings
import os

def check_fire_with_roboflow(image_path):
    """
    Отправляет фото в Roboflow API и возвращает список предсказаний.
    """
    api_key = settings.ROBOFLOW_API_KEY
    model = settings.ROBOFLOW_MODEL_ID
    version = settings.ROBOFLOW_VERSION

    # Формируем URL согласно документации Roboflow
    url = f"https://detect.roboflow.com/{model}/{version}?api_key={api_key}"

    try:
        with open(image_path, "rb") as img_file:
            # Отправляем файл
            response = requests.post(url, files={"file": img_file})

        if response.status_code == 200:
            data = response.json()
            # Возвращаем список предсказаний (ключ 'predictions' из вашего JSON)
            return data.get('predictions', [])
        else:
            print(f"❌ Ошибка Roboflow: {response.text}")
            return []

    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return []