from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import CottonBatch, Machine, MaintenanceLog
from .serializers import CottonBatchSerializer, MachineSerializer, MaintenanceLogSerializer
from users.permissions import IsLabOrReadOnly
from .services import analyze_machine_health, get_agronomy_data, get_coords_by_ip
from .ml_service import hvi_classifier, vision_classifier
import logging

logger = logging.getLogger(__name__)

class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def telemetry_data(self, request, pk=None):
        """Get telemetry data for a specific machine"""
        try:
            machine = Machine.objects.get(pk=pk)
            logs = MaintenanceLog.objects.filter(machine=machine).order_by('-timestamp')[:100]

            telemetry = {
                "timestamps": [log.timestamp.isoformat() for log in logs],
                "temperatures": [float(log.temperature) if log.temperature else 0 for log in logs],
                "vibrations": [float(log.vibration) if log.vibration else 0 for log in logs],
                "humidities": [float(log.humidity) if log.humidity else 0 for log in logs],
                "motor_loads": [float(log.motor_load) if hasattr(log, 'motor_load') and log.motor_load else 0 for log in logs],
            }

            data = {
                "machine": MachineSerializer(machine).data,
                "telemetry": telemetry,
                "count": len(logs)
            }
            return Response(data)
            
        except Machine.DoesNotExist:
            return Response({"error": "Machine not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='telemetry/bulk')
    def telemetry_bulk(self, request):
        """Bulk create telemetry data for machines"""
        from django.utils import timezone as tz
        from datetime import datetime as dt
        
        payload = request.data
        
        if not isinstance(payload, list):
            return Response(
                {"error": "Expected a list of telemetry records"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_count = 0
        errors = []
        
        for idx, record in enumerate(payload):
            try:
                machine_id = record.get('machine_id')
                machine = Machine.objects.get(pk=machine_id)
                
                # Parse timestamp
                timestamp_str = record.get('timestamp')
                if timestamp_str:
                    try:
                        log_timestamp = dt.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        log_timestamp = tz.now()
                else:
                    log_timestamp = tz.now()
                
                # Create maintenance log entry
                MaintenanceLog.objects.create(
                    machine=machine,
                    temperature=record.get('temperature', 0),
                    vibration=record.get('vibration', 0),
                    humidity=record.get('humidity', 0),
                    motor_load=record.get('motor_load', 0),
                    timestamp=log_timestamp,
                    log_type='telemetry',
                    notes='Auto-generated from sensor data'
                )
                
                # Update machine's last readings
                machine.last_temperature = record.get('temperature', 0)
                machine.last_vibration = record.get('vibration', 0)
                machine.last_humidity = record.get('humidity', 0)
                machine.last_motor_load = record.get('motor_load', 0)
                machine.save()
                
                created_count += 1
                
            except Machine.DoesNotExist:
                errors.append(f"Row {idx}: Machine {machine_id} not found")
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
        
        return Response({
            "created": created_count,
            "total": len(payload),
            "errors": errors[:10] if errors else None
        }, status=status.HTTP_200_OK)


class CottonBatchViewSet(viewsets.ModelViewSet):
    queryset = CottonBatch.objects.all()
    serializer_class = CottonBatchSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='predict-quality', permission_classes=[], parser_classes=[JSONParser])
    def predict_quality(self, request):
        """
        HVI Lab - Predict cotton quality from HVI parameters
        
        Expected payload:
        {
            "micronaire": 4.0,
            "strength": 30.0,
            "length": 1.12,
            "uniformity": 83.0,
            "trash_grade": 3,
            "trash_cnt": 15,
            "trash_area": 0.2,
            "sfi": 9.0,
            "sci": 130,
            "color_grade": "31-3"
        }
        """
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['micronaire', 'strength', 'length', 'uniformity', 
                             'trash_grade', 'trash_cnt', 'trash_area', 'sfi', 'sci', 'color_grade']
            
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return Response(
                    {"error": f"Missing required fields: {', '.join(missing_fields)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert to appropriate types
            hvi_data = {
                'micronaire': float(data['micronaire']),
                'strength': float(data['strength']),
                'length': float(data['length']),
                'uniformity': float(data['uniformity']),
                'trash_grade': int(data['trash_grade']),
                'trash_cnt': int(data['trash_cnt']),
                'trash_area': float(data['trash_area']),
                'sfi': float(data['sfi']),
                'sci': float(data['sci']),
                'color_grade': str(data['color_grade'])
            }
            
            # Predict using ML model
            result = hvi_classifier.predict(hvi_data)
            
            return Response({
                "success": True,
                "quality_class": result['quality_class'],
                "confidence": result['confidence'],
                "probabilities": result['probabilities'],
                "input_data": hvi_data
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {"error": f"Invalid data type: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in quality prediction: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='analyze-image', permission_classes=[], parser_classes=[MultiPartParser, FormParser])
    def analyze_image(self, request):
        """
        Computer Vision - Analyze cotton image for cleanliness
        
        Expected: multipart/form-data with 'image' field
        """
        try:
            if 'image' not in request.FILES:
                return Response(
                    {"error": "No image file provided. Send image in 'image' field."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            image_file = request.FILES['image']
            
            # Save temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                for chunk in image_file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            try:
                # Predict using CV model
                result = vision_classifier.predict(tmp_path)
                
                return Response({
                    "success": True,
                    "label": result['label'],
                    "confidence": result['confidence'],
                    "score": result['score'],
                    "filename": image_file.name
                }, status=status.HTTP_200_OK)
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceLog.objects.all().order_by('-timestamp')
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsAuthenticated]


# ==========================================
# 2. STANDALONE VIEWS (ДЛЯ ДАШБОРДА И КАРТЫ)
# ==========================================

def dashboard_view(request):
    """
    Отдает HTML страницу с картой.
    """
    return render(request, 'dashboard.html')


def api_agronomy_predict(request):
    """
    API для карты: принимает Lat/Lon (или определяет по IP) и отдает прогноз.
    """
    # 1. Пробуем взять координаты из клика по карте
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    # 2. Если координат нет (автозагрузка страницы) - определяем по IP
    if not lat or not lon:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Функция из services.py (GeoIP)
        lat, lon, region_name = get_coords_by_ip(ip)

    # 3. Получаем агрономический прогноз
    data = get_agronomy_data(lat, lon)

    return JsonResponse(data)