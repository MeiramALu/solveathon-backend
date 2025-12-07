import os
import django
import pandas as pd
import time
import sys

# Настройка Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from factory.models import Machine, MaintenanceLog
from factory.services import analyze_machine_health


def run_simulation():
    excel_file = 'telemetry.xlsx'

    if not os.path.exists(excel_file):
        print(f"❌ Файл {excel_file} не найден.")
        return

    print(f"📂 Читаем данные из {excel_file}...")
    try:
        df = pd.read_excel(excel_file)
        # Чистим названия колонок (убираем пробелы, делаем маленькими)
        df.columns = df.columns.str.strip().str.lower()
    except Exception as e:
        print(f"❌ Ошибка чтения Excel: {e}")
        return

    print("🚀 Записываем данные в базу...")

    for index, row in df.iterrows():
        try:
            # 1. Читаем данные
            m_name = str(row['machine_id']).strip()

            temp = float(row['temperature'])
            vib = float(row['vibration'])

            # Нагрузка (может называться load или motor_load)
            if 'motor_load' in row:
                load = float(row['motor_load'])
            elif 'load' in row:
                load = float(row['load'])
            else:
                load = 0.0

            # Влажность (если есть в excel)
            if 'humidity' in row:
                hum = float(row['humidity'])
            else:
                hum = 0.0

            # 2. Ищем станок
            machine = Machine.objects.get(name=m_name)

            # 3. Обновляем показатели (Текущее состояние)
            machine.last_temp = temp
            machine.last_vibration = vib
            machine.last_motor_load = load
            machine.last_humidity = hum

            # 4. Анализируем (AI)
            prob, desc = analyze_machine_health(machine, temp, vib, load)

            # Меняем статус
            if prob > 50:
                machine.status = 'WARNING'
            else:
                machine.status = 'ONLINE'

            machine.save()

            # 5. Пишем лог (ИСТОРИЯ ДЛЯ ГРАФИКОВ)
            MaintenanceLog.objects.create(
                machine=machine,
                is_prediction=True,
                probability_failure=prob,
                description=f"Simulated: {desc}",  # <--- ЗАПЯТАЯ ВАЖНА

                # Записываем цифры, чтобы потом строить графики
                temperature=temp,
                vibration=vib
            )

            print(f"✅ {m_name}: T={temp}, Vib={vib}, Risk={prob}%")
            time.sleep(0.1)

        except Machine.DoesNotExist:
            print(f"⚠️ Станок '{m_name}' не найден в базе.")
        except Exception as e:
            print(f"❌ Ошибка в строке {index}: {e}")

    print("\n🏁 Готово! Данные в базе.")


if __name__ == '__main__':
    run_simulation()