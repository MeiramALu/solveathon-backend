from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Route, Vehicle, Field, Depot, OptimizationJob
from .serializers import RouteMapSerializer, VehicleSerializer
from .route_optimization_service import RouteOptimizationService


class LogisticsMapViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint, отдающий только активные маршруты для отрисовки карты
    GET /api/logistics/map-data/
    """
    permission_classes = [AllowAny]
    queryset = Route.objects.filter(is_active=True).select_related('vehicle')
    serializer_class = RouteMapSerializer
    
class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that returns vehicle data.
    GET /api/logistics/vehicles/
    """
    permission_classes = [AllowAny]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def optimize_routes(request):
    """
    POST /api/logistics/optimize/
    
    Optimize cotton harvest routes using OpenRouteService API
    
    Request body:
    {
        "depot": {"lat": 43.0, "lon": 68.0},
        "vehicles": [
            {"id": 1, "name": "Truck 1", "capacity": 50, "shiftMinutes": 480}
        ],
        "fields": [
            {"id": 1, "lat": 43.1, "lon": 68.1, "demand": 10, "serviceTimeMinutes": 30}
        ]
    }
    """
    try:
        service = RouteOptimizationService()
        result = service.optimize_routes(request.data)
        
        # Check if there's an error in the result
        if 'error' in result:
            error_type = result.get('errorType', 'UNKNOWN')
            status_code = status.HTTP_400_BAD_REQUEST
            
            if error_type == 'ORS':
                status_code = result.get('statusCode', status.HTTP_502_BAD_GATEWAY)
            elif error_type in ['TIMEOUT', 'NETWORK']:
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif error_type == 'INTERNAL':
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            return Response(result, status=status_code)
        
        # Success - optionally save to database
        # You can create an OptimizationJob record here if needed
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': f'Internal server error: {str(e)}',
                'errorType': 'INTERNAL'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def ai_summary(request):
    """
    POST /api/logistics/ai-summary/
    
    Generate AI summary of optimization results using Google Gemini
    
    Request body:
    {
        "facts": {
            "totals": {"distance": 100, "time": 120, ...},
            "vehicles": [...],
            "unassignedCount": 0
        }
    }
    """
    try:
        facts = request.data.get('facts')
        
        if not facts:
            return Response(
                {'error': "Missing 'facts' in request body."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = RouteOptimizationService()
        result = service.generate_ai_summary(facts)
        
        # Check if there's an error in the result
        if 'error' in result:
            error_type = result.get('errorType', 'UNKNOWN')
            status_code = status.HTTP_400_BAD_REQUEST
            
            if error_type == 'CONFIG':
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            elif error_type == 'GEMINI':
                status_code = status.HTTP_502_BAD_GATEWAY
            
            return Response(result, status=status_code)
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {
                'error': f'Internal server error: {str(e)}',
                'errorType': 'INTERNAL'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
