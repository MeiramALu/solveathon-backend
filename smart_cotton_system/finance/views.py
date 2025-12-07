from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .services import FinanceAIService


class AIRecommendationView(APIView):
    """
    GET /api/finance/ai-recommendations/
    Returns AI-based trading recommendations with forecast
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            service = FinanceAIService()
            recommendations = service.get_ai_recommendations()
            
            if not recommendations.get('success', False):
                return Response(
                    {"error": recommendations.get('error', 'Unknown error')},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            return Response(recommendations, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForecastView(APIView):
    """
    GET /api/finance/forecast/?days=7
    Returns price forecast for specified days
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
            if days < 1 or days > 30:
                return Response(
                    {"error": "Days must be between 1 and 30"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = FinanceAIService()
            forecast = service.get_forecast(days)
            
            if forecast is None:
                return Response(
                    {"error": "Unable to generate forecast"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            return Response({
                "success": True,
                "forecast": forecast.tolist(),
                "days": days
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
