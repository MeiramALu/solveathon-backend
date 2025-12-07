"""
Test script for Safety Monitoring API
Run this after setting up the backend to verify everything works
"""
import requests
import json
import time

API_BASE = "http://localhost:8000/api/safety"

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_workers_list():
    print_header("Test 1: Get All Workers")
    try:
        response = requests.get(f"{API_BASE}/workers/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            workers = response.json()
            print(f"✅ Found {len(workers)} workers")
            for worker in workers[:3]:  # Show first 3
                print(f"  - {worker['name']} ({worker['role']})")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_live_status():
    print_header("Test 2: Get Live Status with Safety Analysis")
    try:
        response = requests.get(f"{API_BASE}/workers/live_status/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Live status retrieved")
            print(f"  Workers: {len(data['workers'])}")
            print(f"  Risk Level: {data['risk_level']['level']} ({data['risk_level']['percentage']}%)")
            
            # Show a worker with alerts
            for worker in data['workers']:
                if worker.get('alert_panic') or worker.get('alert_fall'):
                    print(f"\n  Worker with alert: {worker['name']}")
                    print(f"    Status: {worker['safety_status']}")
                    break
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_zones():
    print_header("Test 3: Get Hazardous Zones")
    try:
        response = requests.get(f"{API_BASE}/zones/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            zones = response.json()
            print(f"✅ Found {len(zones)} zones")
            for zone in zones:
                print(f"  - {zone['name']} ({zone['zone_type']})")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_simulation():
    print_header("Test 4: Trigger Panic Simulation")
    try:
        # Trigger panic on worker 101
        response = requests.post(
            f"{API_BASE}/workers/simulate/",
            json={"type": "panic", "worker_id": 101}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Simulation triggered: {data['message']}")
            
            # Wait a moment then check status
            time.sleep(1)
            
            response2 = requests.get(f"{API_BASE}/workers/live_status/")
            if response2.status_code == 200:
                data2 = response2.json()
                worker = next((w for w in data2['workers'] if w['worker_id'] == 101), None)
                if worker:
                    print(f"\n  Worker 101 status after simulation:")
                    print(f"    Heart Rate: {worker['heart_rate']} BPM")
                    print(f"    Steps: {worker['steps']}")
                    print(f"    Alert Panic: {worker['alert_panic']}")
                    print(f"    Status: {worker['safety_status']}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_ai_check():
    print_header("Test 5: AI Safety Analysis (requires Gemini API key)")
    try:
        response = requests.get(f"{API_BASE}/workers/101/ai_check/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Analysis received")
            if 'ai_analysis' in data:
                print(f"\n{data['ai_analysis'][:200]}...")
            elif 'fallback_analysis' in data:
                print(f"\n  Fallback: {data['fallback_analysis']}")
        else:
            data = response.json()
            if 'error' in data:
                print(f"⚠️  AI service unavailable (expected if no API key)")
                print(f"  Error: {data['error']}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("\n" + "=" * 60)
    print("  🛡️  SAFETY MONITORING API TEST SUITE")
    print("=" * 60)
    print("\nMake sure Django is running on http://localhost:8000")
    input("Press Enter to continue...")
    
    test_workers_list()
    time.sleep(1)
    
    test_live_status()
    time.sleep(1)
    
    test_zones()
    time.sleep(1)
    
    test_simulation()
    time.sleep(1)
    
    test_ai_check()
    
    print("\n" + "=" * 60)
    print("  ✅ TEST SUITE COMPLETE")
    print("=" * 60)
    print("\nIf all tests passed, your backend is ready!")
    print("Next: Open http://localhost:3000/safety-monitoring")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    main()
