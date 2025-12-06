def classify_cotton_quality(instance):
    """
    Анализ HVI показателей для присвоения класса (Premium, Standard, Low).
    """
    mic = instance.micronaire
    strength = instance.strength
    trash = instance.trash_grade

    if mic is None or strength is None:
        return None

    # Логика оценки
    if (3.7 <= mic <= 4.2) and strength >= 29 and (trash is None or trash <= 3):
        return "Premium (Oliy)"
    elif (mic < 3.5 or mic > 4.9) or strength < 25:
        return "Low Grade (II Sort)"
    else:
        return "Middling (Standard)"


def analyze_machine_health(machine, temp, vibration, load):
    """
    Анализ состояния станка.
    """
    risk_score = 0
    issues = []

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