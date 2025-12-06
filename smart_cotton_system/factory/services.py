import requests
from django.conf import settings
import os


def send_image_to_ml_api(image_path):
    """
    Отправляет файл на внешний сервер и получает результат.
    """
    url = settings.ML_API_URL
    api_key = settings.ML_API_KEY

    # Подготавливаем заголовки (обычно API требует ключ в хедере)
    headers = {
        "Authorization": f"Bearer {api_key}",
        # Иногда требуют "x-api-key": api_key
    }

    # Открываем картинку и отправляем
    try:
        with open(image_path, 'rb') as img_file:
            files = {'file': img_file}  # Имя поля 'file' зависит от документации API

            print(f"📡 Отправляем запрос на {url}...")
            response = requests.post(url, headers=headers, files=files, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✅ Ответ от ML получен:", data)
            return data
        else:
            print(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return None