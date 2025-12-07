import requests
import os
from dotenv import load_dotenv

# Загружаем настройки
load_dotenv()
API_KEY = os.getenv("ROBOFLOW_API_KEY")
MODEL_ID = "safety-helmet-and-reflection-vest-detection"
VERSION = "4"  # Убедитесь, что версия совпадает с settings.py


def debug_roboflow(image_path):
    url = f"https://detect.roboflow.com/{MODEL_ID}/{VERSION}?api_key={API_KEY}"

    print(f"📡 Отправляем запрос в {MODEL_ID}/{VERSION}...")

    with open(image_path, "rb") as img_file:
        response = requests.post(url, files={"file": img_file})

    if response.status_code == 200:
        data = response.json()
        predictions = data.get('predictions', [])
        print("\n🔍 ЧТО ВИДИТ РОБОТ:")
        if not predictions:
            print("❌ ПУСТО! Робот никого не нашел.")
        for p in predictions:
            print(f"   ---> Класс: '{p['class']}' | Уверенность: {p['confidence']}")
    else:
        print(f"❌ Ошибка API: {response.text}")


if __name__ == "__main__":
    # Укажите путь к вашей картинке
    debug_roboflow("worker.jpg")