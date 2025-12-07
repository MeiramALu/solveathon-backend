import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from django.conf import settings

def analyze_water_needs(moisture, temp):
    """
    Принимает влажность (%) и температуру.
    Возвращает (bool, str): (Нужен ли полив, Сообщение).
    """
    if temp is None:
        temp = 25.0 # Средняя температура по умолчанию

    # Логика принятия решений
    # 1. Если влажность 100% (как в вашем файле) -> Полив точно не нужен
    if moisture >= 95:
        return False, "✅ Почва перенасыщена влагой. Полив не требуется."

    # 2. Оптимальная зона (70-90%)
    if 70 <= moisture < 95:
        return False, "💧 Влажность в норме."

    # 3. Начало засухи (меньше 60%)
    if moisture < 60:
        return True, "⚠️ Внимание! Влажность низкая. Рекомендуется полив."

    # 4. Критическая ситуация (меньше 40%)
    if moisture < 40:
        return True, "🔥 КРИТИЧЕСКАЯ ЗАСУХА! Срочно включить полив!"

    return False, "Анализ завершен"

import os
import joblib
import pandas as pd
from datetime import date, timedelta
from django.conf import settings
from .models import SensorReading, IrrigationPrediction, Field
from .ml_models.water_prediction_suite import WaterAISuite

class WaterManagementService:
    """Enhanced service for water management predictions using WaterAISuite"""
    
    def __init__(self):
        model_path = os.path.join(settings.BASE_DIR, 'agronomy', 'ml_models', 'Irrigation_Model.pkl')
        try:
            self.suite = WaterAISuite()
            self.suite.load_model(model_path)
            self.model = self.suite.model
            print(f"Model loaded from {model_path}")
        except FileNotFoundError:
            print(f"Model not found at {model_path}. Train the model first.")
            self.suite = None
            self.model = None
        
        self.dry_threshold = 30.0
        self.target_humidity = 35.0
        self.max_daily_m3_mu = 40.0
        
        self.feature_cols = [
            "soil_humidity(%)",
            "soil_temperature(°C)",
            "rain(mm/day)",
            "daily_mean_temperature(°C)",
            "irrigation_amount(m3/mu)",
            "days_since_irrigation",
            "loc_x",
            "loc_y",
        ]
    
    def predict_humidity(self, sensor_data: dict) -> dict:
        """Predict tomorrow's humidity for given sensor data"""
        if not self.model:
            raise ValueError("Model not loaded. Please train the model first.")
        
        # Convert dict to DataFrame with proper column names
        input_data = {
            "soil_humidity(%)": sensor_data['soil_humidity'],
            "soil_temperature(°C)": sensor_data['soil_temperature'],
            "rain(mm/day)": sensor_data.get('rain', 0),
            "daily_mean_temperature(°C)": sensor_data['daily_mean_temperature'],
            "irrigation_amount(m3/mu)": sensor_data.get('irrigation_amount', 0),
            "days_since_irrigation": sensor_data.get('days_since_irrigation', -1),
            "loc_x": sensor_data['location_x'],
            "loc_y": sensor_data['location_y'],
        }
        
        df = pd.DataFrame([input_data])
        prediction = self.model.predict(df)[0]
        
        dry_risk = prediction < self.dry_threshold
        recommended_irrigation = self._calculate_irrigation(prediction)
        
        return {
            'predicted_humidity': float(prediction),
            'dry_risk': bool(dry_risk),
            'irrigation_action': 'IRRIGATE' if dry_risk else 'SKIP',
            'recommended_irrigation': float(recommended_irrigation),
            'risk_level': self._assess_risk_level(prediction)
        }
    
    def _calculate_irrigation(self, predicted_humidity: float) -> float:
        """Calculate recommended irrigation amount"""
        deficit = max(0, self.target_humidity - predicted_humidity)
        normalized = min(1.0, deficit / self.target_humidity)
        return normalized * self.max_daily_m3_mu
    
    def _assess_risk_level(self, predicted_humidity: float) -> str:
        """Assess risk level based on predicted humidity"""
        if predicted_humidity < 20:
            return 'high'
        elif predicted_humidity < 30:
            return 'medium'
        return 'low'
    
    def simulate_future(self, base_data: dict, days_ahead: int = 7) -> list:
        """Simulate future predictions for multiple days"""
        if not self.model:
            raise ValueError("Model not loaded")
        
        predictions = []
        current_humidity = base_data['soil_humidity']
        current_days_since = base_data.get('days_since_irrigation', -1)
        
        for day in range(1, days_ahead + 1):
            # Prepare features for prediction
            features = {
                "soil_humidity(%)": current_humidity,
                "soil_temperature(°C)": base_data['soil_temperature'],
                "rain(mm/day)": base_data.get('rain', 0),
                "daily_mean_temperature(°C)": base_data['daily_mean_temperature'],
                "irrigation_amount(m3/mu)": 0,  # Assume no irrigation
                "days_since_irrigation": current_days_since + day,
                "loc_x": base_data['location_x'],
                "loc_y": base_data['location_y'],
            }
            
            df = pd.DataFrame([features])
            next_humidity = self.model.predict(df)[0]
            
            prediction_date = date.today() + timedelta(days=day)
            
            predictions.append({
                'date': prediction_date.isoformat(),
                'predicted_humidity': float(next_humidity),
                'dry_risk': bool(next_humidity < self.dry_threshold),
                'recommended_irrigation': float(self._calculate_irrigation(next_humidity)),
                'risk_level': self._assess_risk_level(next_humidity)
            })
            
            current_humidity = next_humidity
        
        return predictions
    
    def bulk_predict_for_field(self, field_id: int, prediction_date=None):
        """Generate predictions for all sensor locations in a field"""
        from .models import SensorReading, IrrigationPrediction, Field
        
        if prediction_date is None:
            prediction_date = date.today()
        
        field = Field.objects.get(id=field_id)
        
        # Get latest sensor readings for this field
        latest_readings = SensorReading.objects.filter(
            field=field,
            date=prediction_date
        ).order_by('location_x', 'location_y')
        
        predictions = []
        
        for reading in latest_readings:
            sensor_data = {
                'soil_humidity': reading.soil_humidity,
                'soil_temperature': reading.soil_temperature,
                'rain': reading.rain,
                'daily_mean_temperature': reading.daily_mean_temperature,
                'irrigation_amount': reading.irrigation_amount,
                'days_since_irrigation': reading.days_since_irrigation,
                'location_x': reading.location_x,
                'location_y': reading.location_y,
            }
            
            result = self.predict_humidity(sensor_data)
            
            # Create or update prediction
            prediction, created = IrrigationPrediction.objects.update_or_create(
                field=field,
                date=prediction_date,
                location_x=reading.location_x,
                location_y=reading.location_y,
                defaults={
                    'predicted_humidity': result['predicted_humidity'],
                    'current_humidity': reading.soil_humidity,
                    'dry_risk': result['dry_risk'],
                    'risk_level': result['risk_level'],
                    'irrigation_action': result['irrigation_action'],
                    'recommended_irrigation': result['recommended_irrigation'],
                }
            )
            
            predictions.append(prediction)
        
        return predictions