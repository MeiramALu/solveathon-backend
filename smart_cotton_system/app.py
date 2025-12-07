import streamlit as st
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
import cv2
from PIL import Image, ImageOps
import os

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Cotton AI Platform",
    page_icon="🌾",
    layout="wide"
)

# --- CSS ДЛЯ КРАСОТЫ (Зеленая тема) ---
st.markdown("""
    <style>
    .main {
        background-color: #f5fdf5;
    }
    .stButton>button {
        background-color: #2e7d32;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌾 Cotton Quality Control & Analytics AI")
st.markdown("Единая платформа для анализа качества хлопка, компьютерного зрения и подбора семян.")

# --- ЗАГРУЗКА МОДЕЛЕЙ (КЭШИРОВАНИЕ) ---
@st.cache_resource
def load_hvi_models():
    try:
        model = joblib.load('models/cotton_xgboost_model.pkl')
        scaler = joblib.load('models/cotton_scaler.pkl')
        enc = joblib.load('models/color_encoder.pkl')
        return model, scaler, enc
    except:
        return None, None, None

@st.cache_resource
def load_cv_model():
    try:
        return tf.keras.models.load_model('models/cotton_model.keras')
    except:
        return None

@st.cache_resource
def load_seed_models():
    try:
        m_yield = joblib.load('models/yield_model.pkl')
        m_qual = joblib.load('models/quality_model.pkl')
        le_loc = joblib.load('models/loc_encoder.pkl')
        le_var = joblib.load('models/var_encoder.pkl')
        return m_yield, m_qual, le_loc, le_var
    except:
        return None, None, None, None

# Загружаем всё при старте
hvi_model, hvi_scaler, hvi_enc = load_hvi_models()
cv_model = load_cv_model()
seed_yield, seed_qual, seed_loc, seed_var = load_seed_models()

# --- ВКЛАДКИ ---
tab1, tab2, tab3 = st.tabs(["📊 1. HVI Лаборатория", "📷 2. Компьютерное зрение", "🌱 3. Подбор Семян"])

# ==========================================
# TAB 1: HVI CLASSIFICATION
# ==========================================
with tab1:
    st.header("Классификация качества волокна (HVI)")
    
    if hvi_model is None:
        st.error("Ошибка: Модели HVI не найдены в папке models/")
    else:
        # Выбор режима ввода
        input_method = st.radio("Способ ввода данных:", ["Вручную", "Загрузка CSV"])
        
        if input_method == "Вручную":
            col1, col2, col3 = st.columns(3)
            with col1:
                mic = st.number_input("Micronaire (Тонина)", 2.0, 6.0, 4.0)
                strength = st.number_input("Strength (Прочность)", 20.0, 40.0, 30.0)
                length = st.number_input("Length (Длина)", 0.9, 1.3, 1.12)
            with col2:
                uniformity = st.number_input("Uniformity (%)", 70.0, 90.0, 83.0)
                trash_grade = st.selectbox("Trash Grade", [1, 2, 3, 4, 5, 6, 7])
                color_grade = st.selectbox("Color Grade", ['11-1', '21-2', '31-3', '41-4', '51-5']) # Добавь свои цвета
            with col3:
                trash_cnt = st.number_input("Trash Count", 0, 100, 15)
                trash_area = st.number_input("Trash Area", 0.0, 5.0, 0.2)
                sfi = st.number_input("SFI", 0.0, 20.0, 9.0)
                sci = st.number_input("SCI", 0.0, 200.0, 130.0)
            
            if st.button("🔍 Анализировать образец"):
                # Подготовка данных
                input_data = pd.DataFrame([{
                    'Micronaire': mic, 'Strength': strength, 'Length': length,
                    'Uniformity': uniformity, 'Trash_Grade': trash_grade,
                    'Trash_Cnt': trash_cnt, 'Trash_Area': trash_area,
                    'SFI': sfi, 'SCI': sci, 'Color_Grade': color_grade
                }])
                
                # Обработка
                try:
                    input_data['Color_Grade'] = hvi_enc.transform(input_data['Color_Grade'])
                    input_data = hvi_scaler.transform(input_data)
                    
                    pred = hvi_model.predict(input_data)[0]
                    probs = hvi_model.predict_proba(input_data)[0]
                    
                    classes = {0: 'Low Grade (Брак) 🔴', 1: 'Premium (Высший) 🟢', 2: 'Standard (Средний) 🟡'}
                    
                    st.subheader(f"Результат: {classes[pred]}")
                    st.progress(int(probs[pred]*100))
                    st.write(f"Уверенность ИИ: {probs[pred]*100:.1f}%")
                    
                except Exception as e:
                    st.error(f"Ошибка при обработке: {e}")

        else:
            uploaded_file = st.file_uploader("Загрузите CSV файл с данными HVI", type="csv")
            if uploaded_file:
                st.info("Функционал массовой обработки готов к интеграции.")
                # Тут можно добавить логику для чтения CSV и predict для всех строк

# ==========================================
# TAB 2: COMPUTER VISION
# ==========================================
with tab2:
    st.header("Определение чистоты хлопка по фото")
    
    if cv_model is None:
        st.error("Ошибка: Модель CV (.keras) не найдена.")
    else:
        uploaded_img = st.file_uploader("Загрузите фото хлопка", type=["jpg", "png", "jpeg"])
        
        if uploaded_img:
            # Показываем фото
            image = Image.open(uploaded_img).convert('RGB')
            st.image(image, caption="Загруженное фото", width=300)
            
            if st.button("📷 Сканировать изображение"):
                # Препроцессинг (как в твоем скрипте)
                img_array = np.array(image)
                # OpenCV resize (чтобы точно совпадало с тренировкой)
                img_resized = cv2.resize(img_array, (224, 224))
                img_batch = np.expand_dims(img_resized, 0) # (1, 224, 224, 3)
                
                # Предикт
                prediction = cv_model.predict(img_batch)
                score = prediction[0][0]
                
                # Логика: 0 - Clean, 1 - Dirty
                if score > 0.5:
                    label = "ГРЯЗНЫЙ (Dirty) 🍂"
                    conf = score
                    color = "red"
                else:
                    label = "ЧИСТЫЙ (Clean) ✨"
                    conf = 1 - score
                    color = "green"
                
                st.markdown(f"<h2 style='color:{color};'>{label}</h2>", unsafe_allow_html=True)
                st.write(f"Вероятность: {conf*100:.2f}%")

# ==========================================
# TAB 3: SEED RECOMMENDATION
# ==========================================
with tab3:
    st.header("Умный подбор семян (Yield Prediction)")
    
    if seed_yield is None:
        st.error("Ошибка: Модели семян (.pkl) не найдены.")
    else:
        # Получаем список локаций из энкодера
        locations = seed_loc.classes_
        selected_loc = st.selectbox("📍 Выберите регион/поле:", locations)
        
        # Словарь описаний (из твоего скрипта)
        varieties_info = {
            'PHY 485WRF': {'type': 'Upland', 'brand': 'PhytoGen (Corteva)'},
            'DP 555 R/R': {'type': 'Upland', 'brand': 'DeltaPine (Monsanto)'},
            'FM 960B2R': {'type': 'Upland', 'brand': 'FiberMax (Bayer)'},
            'STV 4892 BR': {'type': 'Upland', 'brand': 'Stoneville'},
            'DPL 445BR': {'type': 'Upland', 'brand': 'DeltaPine'},
            'TAMCOT 22': {'type': 'Upland', 'brand': 'Tamcot (Texas A&M)'},
            'COBALT': {'type': 'Pima', 'brand': 'Cobalt Pima (Premium)'},
            'DP 340': {'type': 'Pima', 'brand': 'DeltaPine Pima'},
            'PHY 800': {'type': 'Pima', 'brand': 'PhytoGen Pima'}
        }

        if st.button("🌱 Подобрать лучшие семена"):
            loc_code = seed_loc.transform([selected_loc])[0]
            all_vars = seed_var.classes_
            
            results = []
            for var_name in all_vars:
                var_code = seed_var.transform([var_name])[0]
                
                # Предикт
                pred_y = seed_yield.predict([[loc_code, var_code]])[0]
                pred_str = seed_qual.predict([[loc_code, var_code]])[0]
                
                # Инфо
                info = varieties_info.get(var_name, {'type': '-', 'brand': 'Local'})
                price_mul = 1.3 if info['type'] == 'Pima' else 1.0
                score = (pred_y * price_mul) + (pred_str * 5)
                
                results.append({
                    'Сорт': var_name,
                    'Тип': info['type'],
                    'Производитель': info['brand'],
                    'Прогноз урожая (lb/ac)': int(pred_y),
                    'Качество (g/tex)': round(pred_str, 1),
                    'Score': score
                })
            
            # Сортировка и вывод
            results.sort(key=lambda x: x['Score'], reverse=True)
            top3 = results[:3]
            
            st.success(f"Топ-3 рекомендации для {selected_loc}:")
            
            # Красивый вывод карточками
            for i, rec in enumerate(top3):
                with st.container():
                    st.markdown(f"### 🏆 #{i+1} {rec['Сорт']}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Урожайность", f"{rec['Прогноз урожая (lb/ac)']} lb/ac")
                    c2.metric("Качество", f"{rec['Качество (g/tex)']}")
                    c3.write(f"**{rec['Производитель']}**")
                    st.divider()

# --- FOOTER ---
st.markdown("---")
st.caption("🚀 Разработано для Хакатона 2025 | Powered by XGBoost, TensorFlow & Scikit-Learn")