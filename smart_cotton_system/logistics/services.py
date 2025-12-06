import requests
from django.conf import settings
import json


def build_optimal_route(vehicle_id, start_coords, end_coords):
    """
    Отправляет координаты для построения маршрута
    """
    url = f"{settings.ML_API_URL}/route-optimize"
    headers = {
        "Authorization": f"Bearer {settings.ML_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "vehicle_id": vehicle_id,
        "start": start_coords,
        "end": end_coords
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()  # Ожидаем: {"geojson": {...}, "minutes": 45}
    except Exception as e:
        print(f"Logistics ML Error: {e}")

    return None