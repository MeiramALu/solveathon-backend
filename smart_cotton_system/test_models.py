import requests
import os
from dotenv import load_dotenv

# Загружаем ключи из .env
load_dotenv()

API_KEY = os.getenv("ROBOFLOW_API_KEY")

# Данные моделей (из ваших настроек)
FIRE_MODEL = "fire-smoke-spark-jb5ug"
FIRE_VERSION = "7"

PPE_MODEL = "safety-helmet-and-reflection-vest-detection"
PPE_VERSION = "4"


def test_roboflow(image_path, model_id, version):
    print(f"\n--- Тестируем модель: {model_id} (v{version}) ---")

    if not os.path.exists(image_path):
        print(f"❌ Файл {image_path} не найден!")
        return

    url = f"https://detect.roboflow.com/{model_id}/{version}?api_key={API_KEY}"

    try:
        with open(image_path, "rb") as img_file:
            response = requests.post(url, files={"file": img_file})

        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])

            if predictions:
                print(f"✅ Успех! Найдено объектов: {len(predictions)}")
                for p in predictions:
                    print(f"   - Класс: {p['class']} | Точность: {p['confidence']:.2f}")
            else:
                print("⚠️ Ответ получен, но объектов не найдено (попробуйте другое фото).")
        else:
            print(f"❌ Ошибка API: {response.text}")

    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")


if __name__ == "__main__":
    if not API_KEY:
        print("❌ ОШИБКА: Не найден ROBOFLOW_API_KEY в .env файле!")
    else:
        # 1. Тест пожара
        test_roboflow("fire.jpg", FIRE_MODEL, FIRE_VERSION)

        # 2. Тест касок
        test_roboflow("worker.jpg", PPE_MODEL, PPE_VERSION)