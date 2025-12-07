from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .services import MarketAnalyzer

class MarketDataView(APIView):
    """
    GET /api/finance/market/?asset=cotton
    Возвращает график + прогноз.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        asset = request.query_params.get('asset', 'cotton') # 'cotton' or 'currency'
        analyzer = MarketAnalyzer()
        
        try:
            data = analyzer.get_data_with_forecast(asset)
            if not data:
                return Response({"error": "Failed to fetch data"}, status=503)
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class ExportOptimizationView(APIView):
    """
    GET /api/finance/optimize/
    Мок-расчет лучшего маршрута и цены (Smart Logistics Cost).
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # В реальной жизни тут сложная математика. Для хакатона возвращаем готовый сценарий.
        return Response({
            "export_price_usd": 0.84,
            "logistics_cost_per_ton": 120,
            "recommended_destination": "China (Xinjiang Hub)",
            "margin_analysis": [
                {"market": "China", "margin": 150, "transit_time": "5 days"},
                {"market": "Turkey", "margin": 135, "transit_time": "12 days"},
                {"market": "Russia", "margin": 110, "transit_time": "7 days"},
            ]
        })