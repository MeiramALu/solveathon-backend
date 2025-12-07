import requests
from django.conf import settings

def check_with_roboflow(image_path, model_id, version):
    api_key = settings.ROBOFLOW_API_KEY
    url = f"https://detect.roboflow.com/{model_id}/{version}?api_key={api_key}"

    try:
        with open(image_path, "rb") as img_file:
            response = requests.post(url, files={"file": img_file})

        if response.status_code == 200:
            return response.json().get('predictions', [])
        else:
            print(f"❌ Ошибка Roboflow ({model_id}): {response.text}")
            return []
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return []