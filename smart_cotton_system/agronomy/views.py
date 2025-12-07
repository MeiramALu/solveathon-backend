from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .models import Field, SensorLog, SeedVariety, SensorReading, IrrigationPrediction
from .serializers import FieldSerializer, SensorLogSerializer, SeedVarietySerializer, IrrigationPredictionSerializer
from users.permissions import IsFarmer  # Импортируем, если нужно проверять роль
from .services import WaterManagementService
from datetime import datetime, timedelta, date
from django.db import models
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def predict_irrigation(request):
    """Predict irrigation needs for a specific location"""
    service = WaterManagementService()
    
    try:
        result = service.predict_humidity(request.data)
        return Response(result)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def simulate_future_irrigation(request):
    """Simulate future irrigation needs"""
    service = WaterManagementService()
    days_ahead = request.data.get('days_ahead', 7)
    
    try:
        predictions = service.simulate_future(request.data, days_ahead)
        return Response({'predictions': predictions})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def field_irrigation_map(request, field_id):
    """Get irrigation predictions map for a field"""
    service = WaterManagementService()
    prediction_date = request.GET.get('date', date.today().isoformat())
    
    try:
        prediction_date = date.fromisoformat(prediction_date)
        predictions = service.bulk_predict_for_field(field_id, prediction_date)
        
        serializer = IrrigationPredictionSerializer(predictions, many=True)
        return Response({
            'field_id': field_id,
            'date': prediction_date.isoformat(),
            'predictions': serializer.data
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def field_timeseries(request):
    """Get time series data for a specific location in a field"""
    field_id = request.GET.get('field_id')
    loc_x = float(request.GET.get('loc_x'))
    loc_y = float(request.GET.get('loc_y'))
    days_back = int(request.GET.get('days_back', 30))
    
    from datetime import date
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)
    
    # Get historical sensor readings
    readings = SensorReading.objects.filter(
        field_id=field_id,
        location_x=loc_x,
        location_y=loc_y,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Get predictions
    predictions = IrrigationPrediction.objects.filter(
        field_id=field_id,
        location_x=loc_x,
        location_y=loc_y,
        date__gte=start_date
    ).order_by('date')
    
    data = {
        'dates': [],
        'actual_humidity': [],
        'predicted_humidity': [],
        'irrigation': [],
        'risk_levels': []
    }
    
    for reading in readings:
        data['dates'].append(reading.date.isoformat())
        data['actual_humidity'].append(reading.soil_humidity)
        data['irrigation'].append(reading.irrigation_amount)
    
    for pred in predictions:
        if pred.date.isoformat() not in data['dates']:
            data['dates'].append(pred.date.isoformat())
            data['actual_humidity'].append(None)
            data['irrigation'].append(0)
        
        data['predicted_humidity'].append(pred.predicted_humidity)
        data['risk_levels'].append(pred.risk_level)
    
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def field_summary(request, field_id):
    """Get comprehensive summary for a field"""
    from datetime import date
    try:
        field = Field.objects.get(id=field_id)
        today = date.today()
        
        # Get today's predictions
        predictions = IrrigationPrediction.objects.filter(
            field=field,
            date=today
        )
        
        # Calculate statistics
        total_locations = predictions.count()
        high_risk = predictions.filter(risk_level='high').count()
        medium_risk = predictions.filter(risk_level='medium').count()
        needs_irrigation = predictions.filter(irrigation_action='IRRIGATE').count()
        
        # Get recent sensor readings
        recent_readings = SensorReading.objects.filter(
            field=field,
            date=today
        ).order_by('-created_at')[:10]
        
        avg_humidity = predictions.aggregate(
            avg=models.Avg('predicted_humidity')
        )['avg'] or 0
        
        return Response({
            'field_id': field_id,
            'field_name': field.name,
            'date': today.isoformat(),
            'statistics': {
                'total_locations': total_locations,
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'needs_irrigation_count': needs_irrigation,
                'average_predicted_humidity': round(avg_humidity, 2),
            },
            'recent_readings': recent_readings.count()
        })
    except Field.DoesNotExist:
        return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_generate_predictions(request):
    """Generate predictions for all sensor locations in a field"""
    field_id = request.data.get('field_id')
    prediction_date = request.data.get('date')
    
    if not field_id:
        return Response({'error': 'field_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    service = WaterManagementService()
    
    try:
        from datetime import date
        if prediction_date:
            prediction_date = date.fromisoformat(prediction_date)
        else:
            prediction_date = date.today()
        
        predictions = service.bulk_predict_for_field(field_id, prediction_date)
        serializer = IrrigationPredictionSerializer(predictions, many=True)
        
        return Response({
            'field_id': field_id,
            'date': prediction_date.isoformat(),
            'predictions_count': len(predictions),
            'predictions': serializer.data
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_dates(request, field_id):
    """Get all available dates with data for a field"""
    try:
        field = Field.objects.get(id=field_id)
        
        # Get dates from sensor readings
        reading_dates = SensorReading.objects.filter(
            field=field
        ).values_list('date', flat=True).distinct().order_by('date')
        
        # Get dates from predictions
        prediction_dates = IrrigationPrediction.objects.filter(
            field=field
        ).values_list('date', flat=True).distinct().order_by('date')
        
        # Combine and sort
        all_dates = set(list(reading_dates) + list(prediction_dates))
        sorted_dates = sorted(all_dates)
        
        if not sorted_dates:
            return Response({
                'dates': [],
                'first_date': None,
                'last_observed_date': None,
                'last_full_date': None,
            })
        
        # Determine last observed date (from sensor readings)
        last_observed = max(reading_dates) if reading_dates else None
        
        return Response({
            'dates': [d.isoformat() for d in sorted_dates],
            'first_date': sorted_dates[0].isoformat(),
            'last_observed_date': last_observed.isoformat() if last_observed else None,
            'last_full_date': sorted_dates[-1].isoformat(),
        })
    except Field.DoesNotExist:
        return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_map_data(request, field_id):
    """Get map visualization data for a specific date"""
    date_str = request.GET.get('date')
    threshold = request.GET.get('threshold')  # Optional dryness threshold filter
    
    if not date_str:
        return Response({'error': 'date parameter required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        field = Field.objects.get(id=field_id)
        target_date = date.fromisoformat(date_str)
        
        # Get sensor readings for this date
        readings = SensorReading.objects.filter(
            field=field,
            date=target_date
        )
        
        # Get predictions for this date
        predictions = IrrigationPrediction.objects.filter(
            field=field,
            date=target_date
        )
        
        # Create a dictionary for quick lookup
        pred_dict = {
            (p.location_x, p.location_y): p 
            for p in predictions
        }
        
        # Build points data
        points = []
        for reading in readings:
            pred = pred_dict.get((reading.location_x, reading.location_y))
            
            point_data = {
                'loc_x': reading.location_x,
                'loc_y': reading.location_y,
                'soil_humidity': reading.soil_humidity,
                'soil_temp': reading.soil_temperature,
                'rain': reading.rain,
                'air_temp': reading.daily_mean_temperature,
                'irrigation': reading.irrigation_amount,
                'days_since_irrigation': reading.days_since_irrigation,
            }
            
            if pred:
                point_data.update({
                    'pred_humidity': pred.predicted_humidity,
                    'recommended_irrigation': pred.recommended_irrigation,
                    'dry_risk': 1 if pred.dry_risk else 0,
                    'risk_level': pred.risk_level,
                    'action': pred.irrigation_action,
                    'is_future': pred.is_future,
                })
            else:
                point_data.update({
                    'pred_humidity': None,
                    'recommended_irrigation': 0,
                    'dry_risk': 0,
                    'risk_level': 'unknown',
                    'action': 'UNKNOWN',
                    'is_future': False,
                })
            
            # Apply threshold filter if provided (show areas with humidity <= threshold, i.e., dry areas)
            if threshold:
                try:
                    threshold_val = float(threshold)
                    pred_hum = point_data.get('pred_humidity')
                    soil_hum = point_data.get('soil_humidity')
                    
                    # Use predicted humidity if available, otherwise use actual soil humidity
                    humidity_to_check = pred_hum if pred_hum is not None else soil_hum
                    
                    if humidity_to_check is not None and humidity_to_check > threshold_val:
                        continue  # Skip points above threshold (keep only dry areas)
                except ValueError:
                    pass
            
            points.append(point_data)
        
        return Response({
            'date': date_str,
            'field_id': field_id,
            'points': points,
            'total_points': len(points),
        })
    except Field.DoesNotExist:
        return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_date_summary(request, field_id):
    """Get summary statistics for all dates"""
    try:
        field = Field.objects.get(id=field_id)
        
        # Get all dates with predictions
        predictions = IrrigationPrediction.objects.filter(field=field)
        
        # Group by date
        from django.db.models import Avg, Count, Sum
        date_stats = predictions.values('date').annotate(
            avg_pred=Avg('predicted_humidity'),
            risk_count=Sum(models.Case(
                models.When(dry_risk=True, then=1),
                default=0,
                output_field=models.IntegerField()
            )),
            point_count=Count('id')
        ).order_by('date')
        
        # Get last observed date
        last_observed = SensorReading.objects.filter(field=field).aggregate(
            max_date=models.Max('date')
        )['max_date']
        
        days = []
        for stat in date_stats:
            days.append({
                'date': stat['date'].isoformat(),
                'avg_pred': round(stat['avg_pred'], 2) if stat['avg_pred'] else 0,
                'risk_count': stat['risk_count'],
                'point_count': stat['point_count'],
            })
        
        return Response({
            'dates': days,
            'last_observed_date': last_observed.isoformat() if last_observed else None,
        })
    except Field.DoesNotExist:
        return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_location_timeseries(request, field_id):
    """Get time series data for a specific location"""
    loc_x = request.GET.get('loc_x')
    loc_y = request.GET.get('loc_y')
    
    if not loc_x or not loc_y:
        return Response({
            'error': 'loc_x and loc_y parameters required',
            'dates': [],
            'actual': [],
            'pred': [],
            'irrigation': [],
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        field = Field.objects.get(id=field_id)
        target_x = round(float(loc_x), 4)
        target_y = round(float(loc_y), 4)
        
        # Get sensor readings
        readings = SensorReading.objects.filter(
            field=field,
            location_x=target_x,
            location_y=target_y
        ).order_by('date')
        
        # Get predictions
        predictions = IrrigationPrediction.objects.filter(
            field=field,
            location_x=target_x,
            location_y=target_y
        ).order_by('date')
        
        # Get last observed date
        last_observed = readings.aggregate(max_date=models.Max('date'))['max_date']
        
        # Build combined timeline
        reading_dict = {r.date: r for r in readings}
        pred_dict = {p.date: p for p in predictions}
        
        all_dates = sorted(set(list(reading_dict.keys()) + list(pred_dict.keys())))
        
        # Add 7 future dates for AI predictions if we have a last observed date
        if last_observed and all_dates:
            from datetime import timedelta
            max_existing_date = max(all_dates)
            for i in range(1, 8):
                future_date = max_existing_date + timedelta(days=i)
                if future_date not in all_dates:
                    all_dates.append(future_date)
            all_dates = sorted(all_dates)
        
        dates = []
        actual = []
        pred = []
        irrigation = []
        
        for d in all_dates:
            dates.append(d.isoformat())
            
            reading = reading_dict.get(d)
            prediction = pred_dict.get(d)
            
            # Actual humidity (None for future dates)
            if reading and (not last_observed or d <= last_observed):
                actual.append(reading.soil_humidity)
                irrigation.append(reading.irrigation_amount)
            else:
                actual.append(None)
                irrigation.append(0)
            
            # Predicted humidity (for future dates, generate prediction if not exists)
            if prediction:
                pred.append(prediction.predicted_humidity)
            elif last_observed and d > last_observed:
                # For future dates without predictions, use last known prediction or estimate
                if pred_dict:
                    last_pred = sorted(pred_dict.values(), key=lambda p: p.date)[-1]
                    # Simple estimation: slightly decrease humidity over time
                    days_ahead = (d - last_observed).days
                    estimated_humidity = max(10, last_pred.predicted_humidity - (days_ahead * 0.5))
                    pred.append(round(estimated_humidity, 2))
                else:
                    pred.append(None)
            else:
                pred.append(None)
        
        return Response({
            'dates': dates,
            'actual': actual,
            'pred': pred,
            'irrigation': irrigation,
            'last_observed_date': last_observed.isoformat() if last_observed else None,
        })
    except Field.DoesNotExist:
        return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({
            'error': 'Invalid loc_x or loc_y values',
            'dates': [],
            'actual': [],
            'pred': [],
            'irrigation': [],
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': str(e),
            'dates': [],
            'actual': [],
            'pred': [],
            'irrigation': [],
        }, status=status.HTTP_400_BAD_REQUEST)

class SeedVarietyViewSet(viewsets.ModelViewSet):
    """
    Справочник семян.
    """
    queryset = SeedVariety.objects.all()
    serializer_class = SeedVarietySerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='recommend', permission_classes=[])
    def recommend_seeds(self, request):
        """
        Seed Recommendation - Get top 3 seed varieties for a location
        
        Expected payload:
        {
            "location": "Field-A"
        }
        """
        try:
            from factory.ml_service import seed_recommender
            
            location = request.data.get('location')
            
            if not location:
                return Response(
                    {"error": "Location is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get recommendations from ML model
            recommendations = seed_recommender.get_recommendations(location)
            
            return Response({
                "success": True,
                "location": location,
                "recommendations": recommendations
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {"error": f"Invalid location: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error in seed recommendation: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='available-locations', permission_classes=[])
    def available_locations(self, request):
        """
        Get list of available locations for seed recommendations
        """
        try:
            from factory.ml_service import seed_recommender
            
            if not seed_recommender.location_encoder:
                return Response(
                    {"error": "Seed models not loaded"}, 
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            locations = seed_recommender.location_encoder.classes_.tolist()
            
            return Response({
                "success": True,
                "locations": locations
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting locations: {e}")
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FieldViewSet(viewsets.ModelViewSet):
    """
    Поля. Фильтрация: Фермер видит только свои поля.
    """
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Если Фермер -> возвращаем только его поля
        if hasattr(user, 'role') and user.role == 'FARMER':
            return Field.objects.filter(owner=user)
        # Если Админ/Лаборант -> возвращаем всё
        return Field.objects.all()

    def perform_create(self, serializer):
        # При создании поля авто-владелец
        serializer.save(owner=self.request.user)


class SensorLogViewSet(viewsets.ModelViewSet):
    """
    Логи датчиков.
    Здесь тоже добавляем фильтрацию, чтобы фермер видел логи ТОЛЬКО со своих полей.
    """
    serializer_class = SensorLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Берем базовый запрос
        queryset = SensorLog.objects.all().order_by('-timestamp')

        user = self.request.user

        # Если Фермер -> фильтруем логи через поле (field__owner)
        if hasattr(user, 'role') and user.role == 'FARMER':
            return queryset.filter(field__owner=user)

        return queryset