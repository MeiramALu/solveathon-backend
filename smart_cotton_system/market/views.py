from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import MarketPrice
from .serializers import MarketPriceSerializer
import random


class MarketPriceViewSet(viewsets.ModelViewSet):
    """
    Рыночные цены на хлопок.
    """
    queryset = MarketPrice.objects.all().order_by('-date')
    serializer_class = MarketPriceSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """
        Прогноз цен (Имитация AI).
        Заменяет функцию get_forecast из task_3.
        """
        # Здесь должна быть логика обращения к AI
        # Пока сделаем заглушку
        current_price = 1500.00
        forecast_price = current_price * random.uniform(0.95, 1.05)

        trend = "UP" if forecast_price > current_price else "DOWN"

        return Response({
            "current_price": current_price,
            "forecast_next_week": round(forecast_price, 2),
            "trend": trend,
            "ai_message": "Рынок стабилен, ожидается небольшой рост спроса."
        })