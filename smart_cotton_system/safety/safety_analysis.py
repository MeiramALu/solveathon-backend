"""
Safety Analysis Service
Ported from safety_analysis.py - analyzes wearable sensor data for hazardous conditions
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from .models import Zone


def determine_zone(lat: float, lon: float) -> str:
    """
    Determines current zone based on lat/lon coordinates.
    """
    # Try to get zones from database
    zones = Zone.objects.all()
    for zone in zones:
        if zone.contains_point(lat, lon):
            return zone.name
    
    # Fallback to hardcoded zones if DB is empty
    # Zone 1: Chemical Storage (Covers ~20-55 lat/lon)
    if 20 <= lat <= 55 and 20 <= lon <= 55:
        return "Chemical Storage"
    
    # Zone 2: Assembly Line (Covers ~30-50 lat, 60-90 lon)
    if 25 <= lat <= 55 and 65 <= lon <= 95:
        return "Assembly Line"
        
    # Zone 3: Loading Dock (Covers ~60-80 lat, 10-40 lon)
    if 55 <= lat <= 85 and 5 <= lon <= 35:
        return "Loading Dock"
        
    return "Safe Zone"


def analyze_worker_safety(worker_data: Dict) -> Dict:
    """
    Analyzes a single worker's data and returns safety analysis.
    
    Args:
        worker_data: Dict with keys: heart_rate, steps, activity_level, temp_c, 
                     spo2, noise_level, hrv, sleep_score, latitude, longitude, altitude
    
    Returns:
        Dict with alert flags and safety_status
    """
    # Extract values
    hr = worker_data.get('heart_rate', 75)
    steps = worker_data.get('steps', 0)
    activity = worker_data.get('activity_level', 0)
    temp = worker_data.get('temp_c', 36.6)
    spo2 = worker_data.get('spo2', 98)
    noise = worker_data.get('noise_level', 60)
    hrv = worker_data.get('hrv', 50)
    sleep = worker_data.get('sleep_score', 80)
    lat = worker_data.get('latitude', 0)
    lon = worker_data.get('longitude', 0)
    alt = worker_data.get('altitude', 0)
    
    # Initialize alerts
    alerts = {
        'alert_panic': False,
        'alert_fall': False,
        'alert_fatigue': False,
        'alert_environment': False,
        'alert_acoustic': False,
        'alert_geofence': False,
    }
    
    # --- 1. Alert: Panic / Man Down Context ---
    # Logic: High HR + No Steps/Low Activity
    alerts['alert_panic'] = (hr > 110) and (steps < 2)
    
    # --- 2. Alert: Fall (Sudden Stop) ---
    # Logic: 0 steps, no activity, elevated HR
    alerts['alert_fall'] = (steps == 0) and (activity == 0) and (hr > 90)
    
    # --- 3. Alert: Fatigue / Not Fit For Duty ---
    # Logic: Low HRV OR Poor Sleep
    alerts['alert_fatigue'] = (hrv < 30) or (sleep < 50)
    
    # --- 4. Alert: Toxic Environment / Overheat ---
    # Logic: SpO2 < 90% (Hypoxia) OR Temp > 40C
    alerts['alert_environment'] = (spo2 < 90) or (temp > 40)
    
    # --- 5. Alert: Acoustic Danger ---
    # Logic: Noise > 85dB
    alerts['alert_acoustic'] = (noise > 85)
    
    # --- 6. Alert: Geofence / Height ---
    # Logic: Altitude > 3m (Height Risk)
    alerts['alert_geofence'] = (alt > 3)
    
    # Determine zone
    zone = determine_zone(lat, lon)
    
    # Compile safety status
    status_messages = []
    
    if zone != "Safe Zone":
        status_messages.append(f"⚠️ {zone}")
    
    if alerts['alert_panic']:
        status_messages.append("🚨 PANIC: High HR + No Movement")
    if alerts['alert_fall']:
        status_messages.append("🚨 FALL DETECTED: Man Down")
    if alerts['alert_fatigue']:
        status_messages.append("😴 FATIGUE: Not Fit for Duty")
    if alerts['alert_environment']:
        status_messages.append("☠️ TOXIC/HEAT: Environmental Danger")
    if alerts['alert_acoustic']:
        status_messages.append("🔊 ACOUSTIC: Hearing Damage Risk")
    if alerts['alert_geofence']:
        status_messages.append("📏 HEIGHT: Fall Risk")
    
    safety_status = " | ".join(status_messages) if status_messages else "OK"
    
    return {
        **alerts,
        'zone': zone,
        'safety_status': safety_status
    }


def analyze_safety_batch(workers_data: List[Dict]) -> List[Dict]:
    """
    Analyzes multiple workers and returns analysis results.
    
    Args:
        workers_data: List of worker data dictionaries
    
    Returns:
        List of dictionaries with original data + analysis results
    """
    results = []
    for worker in workers_data:
        analysis = analyze_worker_safety(worker)
        results.append({
            **worker,
            **analysis
        })
    return results


def get_risk_level(workers_analysis: List[Dict]) -> Dict:
    """
    Calculate overall site risk level based on worker alerts.
    
    Returns:
        Dict with 'level' ('LOW', 'MODERATE', 'HIGH'), 'percentage', and 'color'
    """
    if not workers_analysis:
        return {'level': 'LOW', 'percentage': 10, 'color': '#00ff9d'}
    
    danger_count = sum(1 for w in workers_analysis 
                       if w.get('alert_panic') or w.get('alert_fall') or w.get('alert_environment'))
    warning_count = sum(1 for w in workers_analysis 
                        if w.get('alert_fatigue') or w.get('alert_acoustic') or w.get('alert_geofence'))
    
    if danger_count > 0:
        percentage = min(90, 50 + danger_count * 15)
        return {'level': 'HIGH', 'percentage': percentage, 'color': '#ff2a2a'}
    elif warning_count > 0:
        percentage = min(50, 25 + warning_count * 8)
        return {'level': 'MODERATE', 'percentage': percentage, 'color': '#ffbe0b'}
    else:
        return {'level': 'LOW', 'percentage': 10, 'color': '#00ff9d'}
