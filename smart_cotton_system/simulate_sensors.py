import pandas as pd
import requests
import time
import json

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/auth/token/login/"
API_URL = f"{BASE_URL}/api/factory/machines/telemetry/"
EXCEL_FILE = "telemetry_new.xlsx"  # Имя вашего файла

# Введите логин и пароль, которые вы создали (admin)
USERNAME = "admin"
PASSWORD = "2031"  # Ваш пароль


def get_auth_token():
    """Получаем токен доступа, чтобы система нас пустила"""
    try:
        response = requests.post(LOGIN_URL, json={"username": USERNAME, "password": PASSWORD})
        if response.status_code == 200:
            token = response.json().get("auth_token")
            print(f"🔑 Успешный вход! Токен: {token[:10]}...")
            return token
        else:
            print(f"❌ Ошибка входа: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        return None


def run_simulation():
    # 1. Получаем токен
    token = get_auth_token()
    if not token:
        return

    headers = {"Authorization": f"Token {token}"}

    # 2. Читаем Excel
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"📂 Загружено {len(df)} строк данных.")
    except Exception as e:
        print(f"❌ Не могу найти файл {EXCEL_FILE}. Положите его в папку проекта.")
        return

    # 3. Отправляем данные построчно
    print("🚀 Начинаем симуляцию датчиков...\n")

    for index, row in df.iterrows():
        # Формируем JSON, который ждет наш API
        payload = {
            "machine_id": row.get("machine_id", "GIN-01"),  # Если в excel нет ID, будет GIN-01
            "temperature": row["temperature"],
            "vibration": row["vibration"],
            "motor_load": row["motor_load"],
            "humidity": row["humidity"]
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                risk = data.get('risk', 0)
                status_icon = "🟢" if risk < 30 else "🔴"
                print(
                    f"[{index + 1}] {status_icon} Отправлено: Temp={payload['temperature']}, Vib={payload['vibration']} -> Риск: {risk}%")
            else:
                print(f"[{index + 1}] ❌ Ошибка API: {response.text}")

        except Exception as e:
            print(f"Ошибка соединения: {e}")

        # Небольшая пауза, чтобы видеть процесс (0.1 секунды)
        time.sleep(0.1)

    print("\n✅ Симуляция завершена!")


if __name__ == "__main__":
    run_simulation()