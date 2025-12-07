import streamlit as st
import pandas as pd
import json
import requests
import plotly.graph_objects as go
import openmeteo_requests
import requests_cache
from retry_requests import retry

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Seed & Yield AI", page_icon="🌱", layout="wide")

# --- 1. ЗАГРУЗКА БАЗЫ СОРТОВ ---
@st.cache_data
def load_varieties():
    try:
        with open('data/cotton_varieties.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# --- 2. НАСТРОЙКА API ---
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# --- 3. ПОЛУЧЕНИЕ ДАННЫХ ---

# А) SOILGRIDS (pH Почвы)
def get_real_soil_ph(lat, lon):
    try:
        url = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property=phh2o&depth=0-5cm"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        # Короткий таймаут, чтобы сайт не вис, если API лежит
        response = requests.get(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            mean_val = data['properties']['layers'][0]['depths'][0]['values']['mean']
            if mean_val is not None:
                return mean_val / 10.0 # Реальный pH
    except Exception:
        pass
    return None

# Б) OPEN-METEO (Погода + Спутник)
@st.cache_data
def get_satellite_data(lat, lon):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2020-04-01",
        "end_date": "2023-10-30",
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                  "soil_temperature_0_to_7cm_mean", "soil_moisture_0_to_7cm_mean"]
    }
    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        daily = response.Daily()
        
        return pd.DataFrame({
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", origin="unix"),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", origin="unix"),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            ),
            "t_max": daily.Variables(0).ValuesAsNumpy(),
            "t_min": daily.Variables(1).ValuesAsNumpy(),
            "rain": daily.Variables(2).ValuesAsNumpy(),
            "soil_temp": daily.Variables(3).ValuesAsNumpy(),
            "soil_moist": daily.Variables(4).ValuesAsNumpy()
        })
    except Exception:
        return pd.DataFrame()

def analyze_soil_condition(df, lat, lon):
    # 1. Пробуем взять реальный pH из API
    real_ph = get_real_soil_ph(lat, lon)
    
    # 2. Фолбэк (Заглушка), если API не отвечает
    is_estimated = False
    if real_ph is None:
        is_estimated = True
        # Атлас резервных значений
        if 40.0 < lat < 42.0 and 67.0 < lon < 69.0: real_ph = 8.1 # Махтаарал
        elif 46.0 < lat < 48.0: real_ph = 8.6 # Атырау (Солончак)
        elif 53.0 < lat < 56.0: real_ph = 7.0 # Север (Чернозем)
        elif 20.0 < lat < 25.0: real_ph = 6.5 # Индия
        else: real_ph = 8.0 # Дефолт

    soil_status = {}
    
    # Логика риска (для расчетов)
    if real_ph > 8.3:
        soil_status['is_salty'] = True
        soil_status['risk_text'] = "Солончак"
    elif real_ph > 7.8:
        soil_status['is_salty'] = False
        soil_status['risk_text'] = "Слабощелочная"
    else:
        soil_status['is_salty'] = False
        soil_status['risk_text'] = "Нейтральная"

    soil_status['ph_val'] = real_ph
    soil_status['is_estimated'] = is_estimated
    
    # Данные по дождям и влажности
    soil_status['moisture_val'] = df['soil_moist'].mean()
    soil_status['summer_rain'] = df[df['date'].dt.month.isin([5,6,7,8])]['rain'].sum() / 4
    soil_status['harvest_rain'] = df[df['date'].dt.month.isin([9,10])]['rain'].sum() / 4
    
    # Текст статуса влажности
    if soil_status['moisture_val'] < 0.15: soil_status['moist_text'] = "Сухо"
    elif soil_status['moisture_val'] > 0.45: soil_status['moist_text'] = "Влажно"
    else: soil_status['moist_text'] = "Норма"
    
    return soil_status

# --- 4. МАТЕМАТИКА ---
def calculate_yield_score(variety, weather_df, soil_status):
    current_yield = variety['max_yield']
    years = weather_df['date'].dt.year.unique()
    yearly_yields = []
    
    for year in years:
        year_df = weather_df[weather_df['date'].dt.year == year]
        
        # 1. ТЕПЛО (GDD)
        year_df['mean_temp'] = (year_df['t_max'] + year_df['t_min']) / 2
        year_df['gdd'] = year_df['mean_temp'] - 12.0
        gdd_sum = year_df[year_df['gdd'] > 0]['gdd'].sum()
        
        if gdd_sum < 800: 
            yearly_yields.append(0)
            continue
            
        gdd_deficit = variety['gdd_needed'] - gdd_sum
        year_penalty = 0
        if gdd_deficit > 0:
            year_penalty += current_yield * (gdd_deficit / variety['gdd_needed'] * 2.0)
            
        # 2. ДОЖДИ (Лето+, Осень-)
        summer_rain = year_df[year_df['date'].dt.month.isin([5, 6, 7, 8])]['rain'].sum()
        if 300 <= summer_rain <= 700:
            year_penalty -= current_yield * 0.10 
        elif summer_rain < 100:
            year_penalty += current_yield * 0.15 

        harvest_rain = year_df[year_df['date'].dt.month.isin([9, 10])]['rain'].sum()
        if harvest_rain > 80:
            year_penalty += current_yield * 0.20 
        
        # 3. ЖАРА
        hot_days = len(year_df[year_df['t_max'] > 40])
        heat_k = 0.2 if variety['heat_tolerance']=='high' else 0.5
        year_penalty += (hot_days * heat_k)
        
        yearly_yields.append(max(0, current_yield - year_penalty))

    if not yearly_yields: return 0.0

    avg_yield = sum(yearly_yields) / len(yearly_yields)
    
    # 4. ПОЧВА (Штраф за pH)
    soil_penalty = 0
    if soil_status['is_salty']:
        if variety['salinity_tolerance'] == 'low':
            soil_penalty = avg_yield * 0.40
        elif variety['salinity_tolerance'] == 'medium':
            soil_penalty = avg_yield * 0.15
            
    return round(max(0, avg_yield - soil_penalty), 1)

# --- 5. ИНТЕРФЕЙС ---
st.sidebar.header("📍 Локация поля")
LOCATIONS = {
    "🇰🇿 Юг (Махтаарал)": (40.8500, 68.6500),
    "🇰🇿 Запад (Атырау)": (47.1127, 51.8869),
    "🇰🇿 Север (Петропавловск)": (54.8753, 69.1628),
    "🇨🇳 Китай (Синьцзян)": (44.3000, 86.0333),
    "🇮🇳 Индия (Муссон)": (21.1458, 79.0882)
}
sel_loc = st.sidebar.selectbox("Быстрый выбор:", ["Вручную"] + list(LOCATIONS.keys()))
if sel_loc != "Вручную":
    st.session_state['lat'], st.session_state['lon'] = LOCATIONS[sel_loc]
lat = st.sidebar.number_input("Широта", value=st.session_state.get('lat', 40.85), format="%.4f")
lon = st.sidebar.number_input("Долгота", value=st.session_state.get('lon', 68.65), format="%.4f")
st.sidebar.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=6)

if st.button("🚀 Рассчитать прогноз", type="primary"):
    with st.spinner("Анализ данных..."):
        
        df = get_satellite_data(lat, lon)
        if df.empty: st.error("Ошибка API."); st.stop()
            
        soil_status = analyze_soil_condition(df, lat, lon)
        avg_t_max = df['t_max'].mean()
        
        # --- МЕТРИКИ (Теперь 5 колонок) ---
        c1, c2, c3, c4, c5 = st.columns(5)
        
        # 1. Температура
        c1.metric("T Воздуха", f"{avg_t_max:.1f}°C")
        
        # 2. Дожди Лето (Польза)
        s_rain = soil_status['summer_rain']
        s_delta = "Засуха" if s_rain < 100 else "Норма"
        c2.metric("Дожди (Лето)", f"{int(s_rain)} мм", s_delta, 
                  delta_color="inverse" if s_rain < 100 else "normal")
        
        # 3. Дожди Сбор (Вред)
        h_rain = soil_status['harvest_rain']
        h_delta = "Опасно!" if h_rain > 50 else "Сухо (ОК)"
        c3.metric("Дожди (Сбор)", f"{int(h_rain)} мм", h_delta, 
                  delta_color="inverse" if h_rain > 50 else "normal")
        
        # 4. Влажность почвы
        moist = soil_status['moisture_val'] * 100
        c4.metric("Влажность", f"{moist:.0f}%", soil_status['moist_text'])
        
        # 5. pH Почвы (Возвращен!)
        ph_label = f"{soil_status['ph_val']}"
        if soil_status['is_estimated']: ph_label += " (Est.)"
        c5.metric("pH Почвы", ph_label, soil_status['risk_text'],
                 delta_color="inverse" if soil_status['is_salty'] else "normal")
        
        st.markdown("---")
        
        varieties = load_varieties()
        results = []
        for v in varieties:
            yld = calculate_yield_score(v, df, soil_status)
            results.append({**v, "predicted": yld})
            
        results.sort(key=lambda x: x['predicted'], reverse=True)
        top = results[:3]
        
        st.subheader("🏆 Рекомендация ИИ")
        cols = st.columns(3)
        for i, col in enumerate(cols):
            if i < len(top):
                item = top[i]
                col.success(f"#{i+1} {item['name']}")
                col.metric("Прогноз", f"{item['predicted']:.1f} ц/га", f"Потенциал: {item['max_yield']}")
                col.caption(f"{item['origin']} | pH-tol: {item['salinity_tolerance']}")

        st.markdown("### 📊 Сравнение эффективности")
        if results:
            fig = go.Figure()
            names = [r['name'] for r in results]
            fig.add_trace(go.Bar(x=names, y=[r['max_yield'] for r in results], name='Потенциал', marker_color='lightgrey'))
            fig.add_trace(go.Bar(x=names, y=[r['predicted'] for r in results], name='Прогноз', marker_color='#2ecc71'))
            fig.update_layout(
                barmode='overlay', 
                height=450,
                xaxis_title="Сорта",
                yaxis_title="Урожайность (ц/га)",
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)