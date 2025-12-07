from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import timedelta
import requests
import json
import os

from .models import SafetyAlert, Worker, WorkerHealthMetrics, Zone
from .serializers import (
    SafetyAlertSerializer, 
    WorkerSerializer, 
    WorkerHealthMetricsSerializer,
    WorkerWithAnalysisSerializer,
    ZoneSerializer
)
from .safety_analysis import analyze_worker_safety, analyze_safety_batch, get_risk_level


class WorkerViewSet(viewsets.ModelViewSet):
    """ViewSet for Worker CRUD and real-time monitoring"""
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    permission_classes = [AllowAny]  # Public access for real-time monitoring
    lookup_field = 'worker_id'  # Use worker_id instead of pk for URL lookups
    
    @action(detail=False, methods=['get'])
    def live_status(self, request):
        """
        Get all workers with live safety analysis.
        Endpoint: /api/safety/workers/live_status/
        """
        workers = Worker.objects.all()
        
        # Convert to dict format for analysis
        workers_data = []
        for worker in workers:
            worker_dict = {
                'worker_id': worker.worker_id,
                'name': worker.name,
                'role': worker.role,
                'latitude': worker.latitude,
                'longitude': worker.longitude,
                'altitude': worker.altitude,
                'heart_rate': worker.heart_rate,
                'steps': worker.steps,
                'activity_level': worker.activity_level,
                'temp_c': worker.temp_c,
                'spo2': worker.spo2,
                'noise_level': worker.noise_level,
                'hrv': worker.hrv,
                'sleep_score': worker.sleep_score,
            }
            workers_data.append(worker_dict)
        
        # Run safety analysis
        analyzed_data = analyze_safety_batch(workers_data)
        
        # Calculate site risk
        risk_info = get_risk_level(analyzed_data)
        
        serializer = WorkerWithAnalysisSerializer(analyzed_data, many=True)
        
        return Response({
            'workers': serializer.data,
            'risk_level': risk_info,
            'timestamp': timezone.now().isoformat()
        })
    
    @action(detail=True, methods=['get'])
    def ai_check(self, request, worker_id=None):
        """
        Run AI-powered safety analysis on a specific worker using Gemini API.
        Endpoint: /api/safety/workers/{id}/ai_check/
        """
        worker = self.get_object()
        
        # Get current analysis
        worker_dict = {
            'worker_id': worker.worker_id,
            'name': worker.name,
            'role': worker.role,
            'latitude': worker.latitude,
            'longitude': worker.longitude,
            'altitude': worker.altitude,
            'heart_rate': worker.heart_rate,
            'steps': worker.steps,
            'activity_level': worker.activity_level,
            'temp_c': worker.temp_c,
            'spo2': worker.spo2,
            'noise_level': worker.noise_level,
            'hrv': worker.hrv,
            'sleep_score': worker.sleep_score,
        }
        
        analysis = analyze_worker_safety(worker_dict)
        
        # Get Gemini API key from environment
        gemini_api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCZc4gl3Hh_rT_LoGOXb8r90btLtrWptUY')
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        # Build prompt for Gemini
        prompt = f"""You are an AI Safety Officer analyzing wearable biosensor data in an industrial facility.

Worker: {worker.name} (ID: {worker.worker_id})
Role: {worker.role}
Current Zone: {analysis['zone']}

Biometric Readings:
- Heart Rate: {worker.heart_rate} BPM
- SpO2: {worker.spo2}%
- Body Temperature: {worker.temp_c}°C
- Heart Rate Variability: {worker.hrv} ms
- Steps (last interval): {worker.steps}
- Activity Level: {worker.activity_level}/10
- Noise Exposure: {worker.noise_level} dB
- Sleep Quality Score: {worker.sleep_score}/100

System Alerts:
- Panic Alert: {analysis['alert_panic']}
- Fall Detection: {analysis['alert_fall']}
- Fatigue Warning: {analysis['alert_fatigue']}
- Environmental Hazard: {analysis['alert_environment']}
- Acoustic Danger: {analysis['alert_acoustic']}

Provide a concise safety analysis:
1. Overall Status (OK/WARNING/CRITICAL)
2. Key Concerns (if any)
3. Immediate Actions Required
4. Preventive Recommendations

Keep response under 200 words, professional tone."""

        try:
            response = requests.post(
                f"{gemini_url}?key={gemini_api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.4,
                        "maxOutputTokens": 500
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data['candidates'][0]['content']['parts'][0]['text']
                
                return Response({
                    'worker_id': worker.worker_id,
                    'name': worker.name,
                    'ai_analysis': ai_response,
                    'current_metrics': worker_dict,
                    'alerts': analysis
                })
            else:
                return Response({
                    'error': 'AI service unavailable',
                    'fallback_analysis': analysis['safety_status']
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
        except Exception as e:
            return Response({
                'error': str(e),
                'fallback_analysis': analysis['safety_status']
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    @action(detail=True, methods=['get'])
    def local_analysis(self, request, worker_id=None):
        """
        Get local safety analysis without AI (fallback).
        Endpoint: /api/safety/workers/{id}/local_analysis/
        """
        worker = self.get_object()
        
        worker_dict = {
            'worker_id': worker.worker_id,
            'name': worker.name,
            'role': worker.role,
            'latitude': worker.latitude,
            'longitude': worker.longitude,
            'altitude': worker.altitude,
            'heart_rate': worker.heart_rate,
            'steps': worker.steps,
            'activity_level': worker.activity_level,
            'temp_c': worker.temp_c,
            'spo2': worker.spo2,
            'noise_level': worker.noise_level,
            'hrv': worker.hrv,
            'sleep_score': worker.sleep_score,
        }
        
        analysis = analyze_worker_safety(worker_dict)
        
        return Response({
            'worker_id': worker.worker_id,
            'name': worker.name,
            'analysis': analysis,
            'current_metrics': worker_dict
        })
    
    @action(detail=False, methods=['post'])
    def simulate(self, request):
        """
        Trigger simulation scenarios for testing.
        Endpoint: /api/safety/workers/simulate/
        Body: {"type": "panic" | "toxic" | "fall" | "reset", "worker_id": 101}
        """
        sim_type = request.data.get('type')
        worker_id = request.data.get('worker_id', 101)
        
        try:
            worker = Worker.objects.get(worker_id=worker_id)
            
            if sim_type == 'panic':
                worker.heart_rate = 135
                worker.steps = 0
                worker.activity_level = 0
            elif sim_type == 'toxic':
                worker.spo2 = 85
                worker.temp_c = 41.5
            elif sim_type == 'fall':
                worker.steps = 0
                worker.activity_level = 0
                worker.heart_rate = 95
                worker.altitude = 0
            elif sim_type == 'reset':
                # Reset to normal values
                worker.heart_rate = 75.0
                worker.steps = 1000
                worker.activity_level = 2
                worker.temp_c = 36.6
                worker.spo2 = 98
                worker.noise_level = 60
                worker.hrv = 50
                worker.altitude = 0
            
            worker.save()
            
            return Response({
                'message': f'Simulation "{sim_type}" applied to worker {worker_id}',
                'worker': WorkerSerializer(worker).data
            })
            
        except Worker.DoesNotExist:
            return Response({
                'error': f'Worker {worker_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)


class WorkerHealthMetricsViewSet(viewsets.ModelViewSet):
    """ViewSet for health metrics time-series data"""
    queryset = WorkerHealthMetrics.objects.all()
    serializer_class = WorkerHealthMetricsSerializer
    permission_classes = [AllowAny]  # Public access for monitoring
    
    @action(detail=False, methods=['get'])
    def by_worker(self, request):
        """Get health metrics for a specific worker"""
        worker_id = request.query_params.get('worker_id')
        hours = int(request.query_params.get('hours', 24))
        
        if not worker_id:
            return Response({'error': 'worker_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            worker = Worker.objects.get(worker_id=worker_id)
            cutoff = timezone.now() - timedelta(hours=hours)
            
            metrics = WorkerHealthMetrics.objects.filter(
                worker=worker,
                timestamp__gte=cutoff
            ).order_by('timestamp')
            
            serializer = self.get_serializer(metrics, many=True)
            return Response(serializer.data)
            
        except Worker.DoesNotExist:
            return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)


class ZoneViewSet(viewsets.ModelViewSet):
    """ViewSet for managing hazardous zones"""
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [AllowAny]  # Public access for zone data


class SafetyAlertViewSet(viewsets.ModelViewSet):
    queryset = SafetyAlert.objects.all().order_by('-timestamp')
    serializer_class = SafetyAlertSerializer

    @action(detail=False, methods=['post'])
    def webhook(self, request):
        """
        Принимает JSON от AI-камеры.
        Ожидаемый формат:
        {
            "location": "Camera_1",
            "predictions": [
                { "class": "Fire-Smoke", "confidence": 0.558, "x": 92, "y": 74, "width": 124, "height": 148 }
            ]
        }
        """
        data = request.data
        location = data.get('location', 'Unknown Camera')
        predictions = data.get('predictions', [])

        alerts_created = []

        for pred in predictions:
            # 1. Фильтр по уверенности (если AI не уверен, не сохраняем)
            conf = pred.get('confidence', 0)
            if conf < 0.4:
                continue

            # 2. Маппинг классов (JSON -> Django Model)
            raw_class = pred.get('class', '')
            alert_type = 'DANGER_ZONE'  # Значение по умолчанию

            if 'Fire' in raw_class or 'Smoke' in raw_class:
                alert_type = 'FIRE'
            elif 'Helmet' in raw_class:
                alert_type = 'NO_HELMET'

            # 3. Создаем запись в БД
            alert = SafetyAlert.objects.create(
                alert_type=alert_type,
                location=location,
                confidence=conf,
                # Сохраняем x, y, w, h прямо в JSON поле, чтобы потом нарисовать квадратик
                detection_details={
                    "x": pred.get('x'),
                    "y": pred.get('y'),
                    "w": pred.get('width'),
                    "h": pred.get('height')
                }
            )
            alerts_created.append(alert.id)

        return Response({
            "status": "processed",
            "alerts_created": len(alerts_created)
        }, status=status.HTTP_201_CREATED)