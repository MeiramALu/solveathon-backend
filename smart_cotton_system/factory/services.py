import random
import requests  # <--- ВАЖНО: Добавлен импорт

# ==========================================
# 1. БАЗА ДАННЫХ СЕМЯН
# ==========================================
COTTON_SEEDS_DB = [
    {"id": "makhtaaral_4", "name": "Махтаарал-4 (KZ)", "origin": "Kazakhstan", "max_yield": 48.0, "days_to_mature": 128,
     "heat_tolerance": "high", "salinity_tolerance": "high"},
    {"id": "turkistan_1", "name": "Туркестан-1 (KZ)", "origin": "Kazakhstan", "max_yield": 40.0, "days_to_mature": 115,
     "heat_tolerance": "high", "salinity_tolerance": "medium"},
    {"id": "m_4011", "name": "М-4011 (KZ)", "origin": "Kazakhstan", "max_yield": 45.0, "days_to_mature": 130,
     "heat_tolerance": "high", "salinity_tolerance": "high"},
    {"id": "xin_lu_zhong_42", "name": "Xin Lu Zhong-42 (CN)", "origin": "China", "max_yield": 60.0,
     "days_to_mature": 135, "heat_tolerance": "medium", "salinity_tolerance": "low"},
    {"id": "xin_lu_zhong_47", "name": "Xin Lu Zhong-47 (CN)", "origin": "China", "max_yield": 65.0,
     "days_to_mature": 140, "heat_tolerance": "medium", "salinity_tolerance": "low"},
    {"id": "s_4727", "name": "C-4727 (Import)", "origin": "Foreign", "max_yield": 55.0, "days_to_mature": 132,
     "heat_tolerance": "medium", "salinity_tolerance": "medium"},
    {"id": "bukhara_6", "name": "Бухара-6 (UZ)", "origin": "Uzbekistan", "max_yield": 43.0, "days_to_mature": 125,
     "heat_tolerance": "high", "salinity_tolerance": "medium"},
    {"id": "sultan", "name": "Султан (UZ)", "origin": "Uzbekistan", "max_yield": 46.0, "days_to_mature": 130,
     "heat_tolerance": "high", "salinity_tolerance": "medium"},
    {"id": "may_455", "name": "May-455 (TR)", "origin": "Turkey", "max_yield": 52.0, "days_to_mature": 135,
     "heat_tolerance": "medium", "salinity_tolerance": "low"},
    {"id": "flash", "name": "Flash (TR)", "origin": "Turkey", "max_yield": 50.0, "days_to_mature": 128,
     "heat_tolerance": "medium", "salinity_tolerance": "low"},
    {"id": "dp_393", "name": "DP-393 (US Proxy)", "origin": "USA", "max_yield": 58.0, "days_to_mature": 138,
     "heat_tolerance": "medium", "salinity_tolerance": "low"},
    {"id": "fibermax_gen", "name": "FiberMax (Generic)", "origin": "Global", "max_yield": 56.0, "days_to_mature": 136,
     "heat_tolerance": "medium", "salinity_tolerance": "medium"}
]


# ==========================================
# 2. АЛГОРИТМ ПОДБОРА СЕМЯН
# ==========================================
def get_seed_recommendations(region_code, soil_ph=7.0):
    scored_seeds = []

    r_lower = str(region_code).lower()
    is_hot_region = 'south' in r_lower or 'юг' in r_lower or 'shymkent' in r_lower or 'turkistan' in r_lower
    is_short_season = 'north' in r_lower or 'север' in r_lower or 'astana' in r_lower

    if not soil_ph: soil_ph = 7.0
    is_salty_soil = (float(soil_ph) > 7.8)

    for seed in COTTON_SEEDS_DB:
        predicted_yield = seed['max_yield']

        if is_salty_soil:
            if seed['salinity_tolerance'] == 'low':
                predicted_yield *= 0.5
            elif seed['salinity_tolerance'] == 'medium':
                predicted_yield *= 0.85

        if is_short_season and seed['days_to_mature'] > 130:
            predicted_yield *= 0.7

        if is_hot_region and seed['heat_tolerance'] == 'low':
            predicted_yield *= 0.9

        predicted_yield = predicted_yield * random.uniform(0.95, 1.05)

        scored_seeds.append({
            'variety': seed['name'],
            'predicted_yield': round(predicted_yield, 1),
            'origin': seed['origin'],
        })

    scored_seeds.sort(key=lambda x: x['predicted_yield'], reverse=True)
    return scored_seeds[:3]


# ==========================================
# 3. GEOIP ЛОГИКА (НОВОЕ!)
# ==========================================
def get_coords_by_ip(ip_address):
    """
    Определяет координаты по IP.
    Если Localhost - возвращает Мактаарал (чтобы работало демо).
    """
    # 1. Если это локальный комп разработчика
    if ip_address in ['127.0.0.1', '::1', 'localhost']:
        # Возвращаем координаты Мактаарала (Юг Казахстана)
        print("🌍 Localhost detected -> Mocking South KZ")
        return 40.8000, 68.6000, "South (Makhtaaral)"

    # 2. Если реальный IP - спрашиваем у бесплатного API
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
        data = response.json()
        if data['status'] == 'success':
            return data['lat'], data['lon'], data['regionName']
    except Exception as e:
        print(f"⚠️ GeoIP Error: {e}")

    # 3. Если всё сломалось - дефолт (Юг)
    return 42.3176, 69.5901, "South (Default)"


# ==========================================
# 4. АГРОНОМИЯ (Обновленная)
# ==========================================
def get_agronomy_data(lat, lon):
    """
    Генерирует погоду по координатам.
    """
    try:
        lat_val = float(lat)
    except:
        lat_val = 42.0

    # Если широта < 43, считаем Югом (Туркестанская область)
    is_south = lat_val < 43.0

    if is_south:
        region_name = 'South (Turkistan)'
        temp = random.randint(32, 42)
        rain = random.randint(0, 5)
        soil_ph = round(random.uniform(7.5, 8.5), 1)
    else:
        region_name = 'North/East'
        temp = random.randint(22, 30)
        rain = random.randint(15, 40)
        soil_ph = round(random.uniform(6.5, 7.5), 1)

    seeds = get_seed_recommendations(region_name, soil_ph)

    return {
        "location_info": region_name,
        "weather": {
            "temp": temp,
            "rain_summer": rain,
            "humidity": random.randint(20, 45),
            "soil_ph": soil_ph
        },
        "recommendations": seeds
    }


# ==========================================
# 5. СТАРЫЕ ФУНКЦИИ (Оставляем)
# ==========================================
def analyze_machine_health(machine, temp, vibration, load):
    risk_score = 0
    issues = []
    if temp > 90:
        risk_score += 50; issues.append("Критический перегрев!")
    elif temp > 75:
        risk_score += 20; issues.append("Высокая температура")
    if vibration > 0.5: risk_score += 40; issues.append("Сильная вибрация")
    if load > 95: risk_score += 30; issues.append("Перегрузка мотора")
    return min(risk_score, 100), ", ".join(issues) if issues else "Показатели в норме"


def classify_hvi_quality(batch_instance):
    mic = batch_instance.micronaire
    strength = batch_instance.strength
    if mic and (3.7 <= mic <= 4.2) and strength and strength >= 29:
        return "Premium (Высший) 🟢"
    elif mic and (mic < 3.5 or mic > 4.9):
        return "Low Grade (Брак) 🔴"
    else:
        return "Standard (Средний) 🟡"


def analyze_cotton_image(image_path):
    conf = random.uniform(0.85, 0.99)
    return ("Dirty (Грязный) 🍂", conf) if random.random() > 0.8 else ("Clean (Чистый) ✨", conf)