import random


# ==========================================
# ЧАСТЬ 1: SMART FACTORY (Анализ станков)
# ==========================================
def analyze_machine_health(machine, temp, vibration, load):
    """
    Анализ телеметрии станка.
    Определяет риск поломки на основе температуры и вибрации.
    """
    risk_score = 0
    issues = []

    # Логика анализа
    if temp > 90:
        risk_score += 50
        issues.append("Критический перегрев!")
    elif temp > 75:
        risk_score += 20
        issues.append("Высокая температура")

    if vibration > 0.5:
        risk_score += 40
        issues.append("Сильная вибрация")

    if load > 95:
        risk_score += 30
        issues.append("Перегрузка мотора")

    probability = min(risk_score, 100)
    description = ", ".join(issues) if issues else "Показатели в норме"

    return probability, description


# ==========================================
# ЧАСТЬ 2: COTTON QUALITY AI (Хлопок)
# ==========================================
def classify_hvi_quality(batch_instance):
    """
    Классификация качества волокна (HVI).
    Имитация ML-модели (XGBoost) для стабильности демо.
    """
    mic = batch_instance.micronaire
    strength = batch_instance.strength

    # Логика HVI
    if mic and (3.7 <= mic <= 4.2) and strength and strength >= 29:
        return "Premium (Высший) 🟢"
    elif mic and (mic < 3.5 or mic > 4.9):
        return "Low Grade (Брак) 🔴"
    else:
        return "Standard (Средний) 🟡"


def analyze_cotton_image(image_path):
    """
    Компьютерное зрение (CV).
    Анализ чистоты хлопка по фото.
    """
    # Имитируем уверенность нейросети
    confidence = random.uniform(0.85, 0.99)

    # Случайный результат (для демо)
    # 80% что чистый, 20% что грязный
    if random.random() > 0.8:
        return "Dirty (Грязный) 🍂", confidence
    else:
        return "Clean (Чистый) ✨", confidence


# ==========================================
# ЧАСТЬ 3: SEED RECOMMENDATION (Семена)
# ==========================================
def get_seed_recommendations(region_name):
    """
    Рекомендация семян на основе региона.
    """
    # База данных сортов
    seeds_db = [
        {'variety': 'PHY 485WRF', 'yield': 1450},
        {'variety': 'DP 555 R/R', 'yield': 1420},
        {'variety': 'FM 960B2R', 'yield': 1380},
        {'variety': 'STV 4892 BR', 'yield': 1350},
        {'variety': 'Cobalt Pima', 'yield': 1200},
    ]

    # Добавляем случайность для реалистичности
    for seed in seeds_db:
        seed['predicted_yield'] = seed['yield'] + random.randint(-50, 50)

    # Сортируем и возвращаем топ-3
    seeds_db.sort(key=lambda x: x['predicted_yield'], reverse=True)
    return seeds_db[:3]