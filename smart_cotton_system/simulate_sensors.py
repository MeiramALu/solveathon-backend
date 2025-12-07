import os
import django
import pandas as pd
import time
from datetime import datetime

# --- НАСТРОЙКИ ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/auth/token/login/"
API_URL = f"{BASE_URL}/api/factory/machines/telemetry/bulk/"
MACHINES_API_URL = f"{BASE_URL}/api/factory/machines/"
EXCEL_FILE = "telemetry_new.xlsx"

USERNAME = "admin"
PASSWORD = "2031"


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


def get_machine_mapping(headers):
    """Fetch all machines and create name-to-id mapping"""
    try:
        response = requests.get(MACHINES_API_URL, headers=headers)
        if response.status_code == 200:
            machines = response.json()
            # Create mapping: machine name -> machine id
            mapping = {}
            for machine in machines:
                name = machine.get('name', '')
                machine_id = machine.get('id')
                if name and machine_id:
                    mapping[name] = machine_id
            print(f"🔧 Загружено {len(mapping)} машин из базы")
            print(f"📋 Машины: {list(mapping.keys())}")
            return mapping
        else:
            print(f"⚠️ Не удалось загрузить список машин: {response.status_code}")
            return {}
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке машин: {e}")
        return {}


def parse_machine_id(value, machine_mapping):
    """Parse machine_id - handle both numeric IDs and machine names"""
    if pd.isna(value):
        return 1  # default
    
    # Try as numeric ID first
    try:
        return int(value)
    except (ValueError, TypeError):
        pass
    
    # Try as machine name
    machine_name = str(value).strip()
    if machine_name in machine_mapping:
        return machine_mapping[machine_name]
    
    # Try partial match (e.g., "GIN-10" matches "Gin Machine 10")
    for name, mid in machine_mapping.items():
        if machine_name.lower() in name.lower() or name.lower() in machine_name.lower():
            return mid
    
    # Default fallback
    print(f"⚠️ Машина '{value}' не найдена, используем ID=1")
    return 1


def parse_excel_data(df, machine_mapping):
    """Parse and validate Excel data"""
    print(f"📊 Столбцы в файле: {df.columns.tolist()}")
    print(f"📊 Первые строки данных:\n{df.head()}\n")
    
    # Clean and prepare data
    payload = []
    skipped = 0
    
    for idx, row in df.iterrows():
        try:
            # Get machine_id from various possible column names
            machine_id_raw = row.get("machine_id", row.get("Machine ID", row.get("machine", row.get("Machine", None))))
            
            record = {
                "machine_id": parse_machine_id(machine_id_raw, machine_mapping),
                "temperature": float(row.get("temperature", row.get("Temperature", row.get("temp", 0)))),
                "vibration": float(row.get("vibration", row.get("Vibration", row.get("vib", 0)))),
                "humidity": float(row.get("humidity", row.get("Humidity", row.get("hum", 0)))),
                "motor_load": float(row.get("motor_load", row.get("Motor Load", row.get("load", 0)))),
            }
            
            # Handle timestamp if present
            timestamp_col = row.get("timestamp", row.get("Timestamp", row.get("time", row.get("Time", None))))
            if timestamp_col is not None and pd.notna(timestamp_col):
                if isinstance(timestamp_col, str):
                    record["timestamp"] = timestamp_col
                else:
                    record["timestamp"] = timestamp_col.isoformat()
            
            payload.append(record)
            
        except Exception as e:
            print(f"⚠️ Ошибка в строке {idx}: {e}")
            skipped += 1
            continue
    
    if skipped > 0:
        print(f"⚠️ Пропущено строк с ошибками: {skipped}")
    
    return payload


def run_simulation():
    excel_file = 'telemetry.xlsx'

    if not os.path.exists(excel_file):
        print(f"❌ Файл {excel_file} не найден.")
        return

    headers = {"Authorization": f"Token {token}"}

    # 2. Загружаем маппинг машин
    machine_mapping = get_machine_mapping(headers)

    # 3. Читаем Excel
    try:
        df = pd.read_excel(excel_file)
        # Чистим названия колонок (убираем пробелы, делаем маленькими)
        df.columns = df.columns.str.strip().str.lower()
    except Exception as e:
        print(f"❌ Не могу найти файл {EXCEL_FILE}: {e}")
        return

    # 4. Парсим данные
    payload = parse_excel_data(df, machine_mapping)
    
    if not payload:
        print("❌ Нет валидных данных для отправки")
        return
    
    print(f"\n📦 Подготовлено {len(payload)} записей для отправки")
    print(f"📝 Пример первой записи: {payload[0]}\n")

    # 5. Отправляем данные в bulk
    print("🚀 Отправляем данные в bulk...\n")

    try:
        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Данные успешно отправлены!")
            print(f"📊 Создано записей: {result.get('created', 0)}")
            if result.get('errors'):
                print(f"⚠️ Ошибки: {result.get('errors')}")
        else:
            print(f"❌ Ошибка API ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")

    print("\n✅ Симуляция завершена!")


if __name__ == '__main__':
    run_simulation()