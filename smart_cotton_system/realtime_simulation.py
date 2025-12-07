"""
Real-time Sensor Data Simulation
Continuously generates and stores sensor data for factory machines
Run this script in the background while the Django server is running
"""

import os
import django
import time
import random
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from factory.models import Machine
from factory.ml_service import analyze_machine_health

def simulate_sensor_reading(machine):
    """Generate realistic sensor readings with slight variations"""
    # Base values with some randomness
    temp_base = 70 + random.uniform(-5, 15)
    vibration_base = 0.15 + random.uniform(-0.05, 0.15)
    motor_load_base = 45 + random.uniform(-10, 20)
    humidity_base = 60 + random.uniform(-10, 15)
    
    # Add occasional anomalies (5% chance)
    if random.random() < 0.05:
        temp_base += random.uniform(10, 20)  # Overheat
        vibration_base += random.uniform(0.1, 0.3)  # High vibration
    
    return {
        'temperature': round(temp_base, 2),
        'vibration': round(vibration_base, 3),
        'motor_load': round(motor_load_base, 1),
        'humidity': round(humidity_base, 1)
    }

def update_machine_data(machine, sensor_data):
    """Update machine with new sensor readings"""
    machine.last_temp = sensor_data['temperature']
    machine.last_vibration = sensor_data['vibration']
    machine.last_motor_load = sensor_data['motor_load']
    machine.last_humidity = sensor_data['humidity']
    machine.timestamp = datetime.now()
    machine.save()
    
    # Analyze health and create maintenance log if needed
    analyze_machine_health(machine)

def main():
    """Main simulation loop"""
    print("🚀 Starting real-time factory sensor simulation...")
    print("Press Ctrl+C to stop")
    
    # Get all machines
    machines = list(Machine.objects.all())
    
    if not machines:
        print("⚠️  No machines found in database. Run migrations and create machines first.")
        return
    
    print(f"✅ Found {len(machines)} machines")
    print(f"📊 Generating sensor data every 3 seconds...\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{timestamp}] Iteration #{iteration}")
            print("-" * 60)
            
            for machine in machines:
                # Generate sensor readings
                sensor_data = simulate_sensor_reading(machine)
                
                # Update machine
                update_machine_data(machine, sensor_data)
                
                # Display status
                status_emoji = "🟢" if machine.status == "ONLINE" else "🟡" if machine.status == "WARNING" else "🔴"
                print(f"{status_emoji} {machine.name:<20} | "
                      f"T: {sensor_data['temperature']:6.2f}°C | "
                      f"V: {sensor_data['vibration']:5.3f}G | "
                      f"L: {sensor_data['motor_load']:5.1f}% | "
                      f"H: {sensor_data['humidity']:5.1f}%")
            
            # Wait before next iteration
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulation stopped by user")
        print(f"✅ Generated {iteration} iterations of sensor data")

if __name__ == '__main__':
    main()
